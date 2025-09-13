import json
import os
import logging

from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

logger = logging.getLogger(__name__)


class CertManager:
    """Certificate manager for generating and managing TLS certificates
    
    Handles CA certificate creation, server certificates, and client certificates
    for mutual TLS authentication.
    """
    TLS_CONFIG_FILE = "rk800keys.json"
    CA_VALIDITY_DAYS = 3650  # 10 years
    CERT_VALIDITY_DAYS = 3650  # 10 years

    def get_server_tls_config(self) -> dict:
        """Get server TLS configuration
        
        Returns:
            dict: server key, cert, and CA cert for TLS setup
        """
        config = self.load_or_create_tls_config()
        return {
            "server_key": config["server_key"],
            "server_cert": config["server_cert"],
            "ca_cert": config["ca_cert"],
        }

    def load_or_create_tls_config(self) -> dict:
        """Load existing TLS config or create new certificates
        
        Returns:
            dict: complete TLS configuration with all certificates and keys
        """
        path = Path.cwd() / self.TLS_CONFIG_FILE
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as file:
                    config = json.load(file)
                if self._validate_ca_cert(config):
                    return config
                logger.info("CA or server certificate expired or invalid, regenerating")
                path.unlink()
            except (json.JSONDecodeError, KeyError, OSError):
                logger.info("Invalid TLS config file, regenerating")
                path.unlink(missing_ok=True)

        config = self._generate_ca_keys_dict()
        temp_path = path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=2)
        os.chmod(temp_path, 0o600)
        temp_path.replace(path)
        logger.info(f"Generated new CA certificate in {path}")
        return config

    def generate_client_cert(self) -> dict:
        """Generate new client certificate signed by CA
        
        Returns:
            dict: client key, cert, and CA cert for client authentication
        """
        config = self.load_or_create_tls_config()
        try:
            ca_key_obj = serialization.load_pem_private_key(
                config["ca_key"].encode(), password=None
            )
            ca_cert_obj = x509.load_pem_x509_certificate(config["ca_cert"].encode())
        except (ValueError, TypeError) as error:
            raise ValueError(f"Failed to load CA keys: {error}") from error

        client_key, client_cert = self._generate_client_cert(ca_key_obj, ca_cert_obj)
        return {
            "client_key": self._serialize_private_key(client_key),
            "client_cert": self._serialize_certificate(client_cert),
            "ca_cert": config["ca_cert"],
        }

    def _now(self):
        """Get current UTC time
        
        Returns:
            datetime: current UTC datetime
        """
        return datetime.now(timezone.utc)

    def _create_key_usage(
        self,
        digital_signature=False,
        key_encipherment=False,
        key_cert_sign=False,
        crl_sign=False,
    ):
        """Create X.509 key usage extension
        
        Args:
            digital_signature (bool): enable digital signature usage
            key_encipherment (bool): enable key encipherment usage
            key_cert_sign (bool): enable certificate signing usage
            crl_sign (bool): enable CRL signing usage
            
        Returns:
            x509.KeyUsage: configured key usage extension
        """
        return x509.KeyUsage(
            digital_signature=digital_signature,
            content_commitment=False,
            key_encipherment=key_encipherment,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=key_cert_sign,
            crl_sign=crl_sign,
            encipher_only=False,
            decipher_only=False,
        )

    def _serialize_private_key(self, private_key):
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    def _serialize_certificate(self, certificate):
        """Serialize certificate to PEM format
        
        Args:
            certificate: cryptography certificate object
            
        Returns:
            str: PEM encoded certificate
        """
        return certificate.public_bytes(serialization.Encoding.PEM).decode()

    def _generate_ca_cert(self):
        """Generate CA certificate and private key
        
        Returns:
            tuple: CA private key and certificate objects
        """
        ca_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ROOT-CA")])
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(self._now())
            .not_valid_after(self._now() + timedelta(days=self.CA_VALIDITY_DAYS))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .add_extension(
                self._create_key_usage(key_cert_sign=True, crl_sign=True),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
                critical=False,
            )
        )
        ca_cert = builder.sign(ca_key, hashes.SHA256())
        return ca_key, ca_cert

    def _generate_client_cert(self, ca_key, ca_cert):
        """Generate client certificate signed by CA
        
        Args:
            ca_key: CA private key object
            ca_cert: CA certificate object
            
        Returns:
            tuple: client private key and certificate objects
        """
        client_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CLIENT")])
        now = self._now()
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(client_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=self.CERT_VALIDITY_DAYS))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .add_extension(
                self._create_key_usage(digital_signature=True),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(client_key.public_key()),
                critical=False,
            )
        )
        client_cert = builder.sign(ca_key, hashes.SHA256())
        return client_key, client_cert

    def _generate_server_cert(self, ca_key, ca_cert):
        """Generate server certificate signed by CA
        
        Args:
            ca_key: CA private key object
            ca_cert: CA certificate object
            
        Returns:
            tuple: server private key and certificate objects
        """
        server_key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "RK800-SERVER")])
        now = self._now()
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=self.CERT_VALIDITY_DAYS))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .add_extension(
                self._create_key_usage(digital_signature=True),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.UniformResourceIdentifier("urn:rk800:service:control")]
                ),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()),
                critical=False,
            )
        )
        server_cert = builder.sign(ca_key, hashes.SHA256())
        return server_key, server_cert

    def _generate_ca_keys_dict(self):
        """Generate complete CA and server certificate set
        
        Returns:
            dict: CA key, CA cert, server key, and server cert in PEM format
        """
        ca_key, ca_cert = self._generate_ca_cert()
        server_key, server_cert = self._generate_server_cert(ca_key, ca_cert)
        return {
            "ca_key": self._serialize_private_key(ca_key),
            "ca_cert": self._serialize_certificate(ca_cert),
            "server_key": self._serialize_private_key(server_key),
            "server_cert": self._serialize_certificate(server_cert),
        }

    def _validate_ca_cert(self, config: dict) -> bool:
        """Validate CA and server certificates are valid and not expired
        
        Args:
            config (dict): TLS configuration with certificates
            
        Returns:
            bool: True if certificates are valid, False otherwise
        """
        try:
            logger.debug("Starting CA certificate validation")
            
            required_keys = ["ca_cert", "ca_key", "server_cert", "server_key"]
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                logger.warning(f"Missing required keys in config: {missing_keys}")
                return False
            logger.debug("All required keys present in config")

            logger.debug("Loading CA certificate")
            ca_cert = x509.load_pem_x509_certificate(config["ca_cert"].encode())
            logger.debug("Loading server certificate")
            server_cert = x509.load_pem_x509_certificate(config["server_cert"].encode())
            now = self._now()
            logger.debug(f"Current time: {now}")

            # Convert certificate times to timezone-aware for comparison
            ca_not_before = ca_cert.not_valid_before.replace(tzinfo=timezone.utc)
            ca_not_after = ca_cert.not_valid_after.replace(tzinfo=timezone.utc)
            server_not_before = server_cert.not_valid_before.replace(tzinfo=timezone.utc)
            server_not_after = server_cert.not_valid_after.replace(tzinfo=timezone.utc)

            logger.debug(f"CA cert valid from {ca_not_before} to {ca_not_after}")
            if ca_not_after <= now:
                logger.warning(f"CA certificate expired: {ca_not_after} <= {now}")
                return False
            if ca_not_before > now:
                logger.warning(f"CA certificate not yet valid: {ca_not_before} > {now}")
                return False
            logger.debug("CA certificate time validity OK")

            logger.debug(f"Server cert valid from {server_not_before} to {server_not_after}")
            if server_not_after <= now:
                logger.warning(f"Server certificate expired: {server_not_after} <= {now}")
                return False
            if server_not_before > now:
                logger.warning(f"Server certificate not yet valid: {server_not_before} > {now}")
                return False
            logger.debug("Server certificate time validity OK")

            logger.debug(f"CA cert subject: {ca_cert.subject}")
            logger.debug(f"Server cert issuer: {server_cert.issuer}")
            if server_cert.issuer != ca_cert.subject:
                logger.warning(f"Server certificate issuer mismatch: {server_cert.issuer} != {ca_cert.subject}")
                return False
            logger.debug("Certificate chain validation OK")

            logger.info("CA certificate validation successful")
            return True
        except (ValueError, TypeError, KeyError) as error:
            logger.error(f"Exception during CA certificate validation: {type(error).__name__}: {error}")
            return False
