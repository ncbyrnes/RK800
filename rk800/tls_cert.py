import json
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID


class CertManager:
    TLS_CONFIG_FILE = "rk800keys.json"
    CA_VALIDITY_DAYS = 3650  # 10 years
    CERT_VALIDITY_DAYS = 3650  # 10 years

    def get_server_tls_config(self) -> dict:
        config = self.load_or_create_tls_config()
        return {
            "server_key": config["server_key"],
            "server_cert": config["server_cert"],
            "ca_cert": config["ca_cert"],
        }

    def load_or_create_tls_config(self) -> dict:
        path = Path.cwd() / self.TLS_CONFIG_FILE
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as file:
                    config = json.load(file)
                if self._validate_ca_cert(config):
                    return config
                print("CA or server certificate expired or invalid, regenerating")
                path.unlink()
            except (json.JSONDecodeError, KeyError, OSError):
                print("Invalid TLS config file, regenerating")
                path.unlink(missing_ok=True)

        config = self._generate_ca_keys_dict()
        temp_path = path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=2)
        os.chmod(temp_path, 0o600)
        temp_path.replace(path)
        print(f"Generated new CA certificate in {path}")
        return config

    def generate_client_cert(self) -> dict:
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
        return datetime.now(timezone.utc)

    def _create_key_usage(
        self,
        digital_signature=False,
        key_encipherment=False,
        key_cert_sign=False,
        crl_sign=False,
    ):
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
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    def _serialize_certificate(self, certificate):
        return certificate.public_bytes(serialization.Encoding.PEM).decode()

    def _generate_ca_cert(self):
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
        ca_key, ca_cert = self._generate_ca_cert()
        server_key, server_cert = self._generate_server_cert(ca_key, ca_cert)
        return {
            "ca_key": self._serialize_private_key(ca_key),
            "ca_cert": self._serialize_certificate(ca_cert),
            "server_key": self._serialize_private_key(server_key),
            "server_cert": self._serialize_certificate(server_cert),
        }

    def _validate_ca_cert(self, config: dict) -> bool:
        try:
            required_keys = ["ca_cert", "ca_key", "server_cert", "server_key"]
            if not all(key in config for key in required_keys):
                return False

            ca_cert = x509.load_pem_x509_certificate(config["ca_cert"].encode())
            server_cert = x509.load_pem_x509_certificate(config["server_cert"].encode())
            now = self._now()

            if ca_cert.not_valid_after_utc <= now or ca_cert.not_valid_before_utc > now:
                return False
            if (
                server_cert.not_valid_after_utc <= now
                or server_cert.not_valid_before_utc > now
            ):
                return False
            if server_cert.issuer != ca_cert.subject:
                return False

            return True
        except (ValueError, TypeError, KeyError):
            return False
