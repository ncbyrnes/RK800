#!/usr/bin/env python3

import json
import datetime
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.x509.oid import NameOID


class TLSManager:
    TLS_CONFIG_FILE = "rk800keys.json"
    CERT_VALIDITY_DAYS = 3650000
    
    def _generate_ca_cert(self) -> tuple:
        ca_key = ec.generate_private_key(ec.SECP256R1())
        ca_subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "ROOT-CA"),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            ca_subject
        ).issuer_name(
            ca_subject
        ).public_key(
            ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=self.CERT_VALIDITY_DAYS)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        ).sign(ca_key, algorithm=None)
        
        return ca_key, ca_cert

    def _generate_client_cert(self, ca_key, ca_cert) -> tuple:
        client_key = ec.generate_private_key(ec.SECP256R1())
        client_subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "DAEMON"),
        ])
        
        client_cert = x509.CertificateBuilder().subject_name(
            client_subject
        ).issuer_name(
            ca_cert.subject
        ).public_key(
            client_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=self.CERT_VALIDITY_DAYS)
        ).sign(ca_key, algorithm=None)
        
        return client_key, client_cert

    def _generate_server_keys(self) -> dict:
        ca_key, ca_cert = self._generate_ca_cert()
        ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM)
        
        ca_key_pem = ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return {
            "ca_key": ca_key_pem.decode('utf-8'),
            "ca_cert": ca_cert_pem.decode('utf-8')
        }

    def generate_client_cert(self) -> dict:
        config = self.load_or_create_tls_config()
        
        ca_key_obj = serialization.load_pem_private_key(
            config["ca_key"].encode('utf-8'),
            password=None
        )
        ca_cert_obj = x509.load_pem_x509_certificate(
            config["ca_cert"].encode('utf-8')
        )
        
        client_key, client_cert = self._generate_client_cert(ca_key_obj, ca_cert_obj)
        
        client_key_pem = client_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        client_cert_pem = client_cert.public_bytes(serialization.Encoding.PEM)
        
        return {
            "tls_priv_key": client_key_pem.decode('utf-8'),
            "tls_cert": client_cert_pem.decode('utf-8'),
            "tls_ca_cert": config["ca_cert"]
        }
    
    def load_or_create_tls_config(self) -> dict:
        config_path = Path.cwd() / self.TLS_CONFIG_FILE
        
        if config_path.exists():
            with open(config_path, 'r') as file:
                return json.load(file)
        else:
            server_config = self._generate_server_keys()
            with open(config_path, 'w') as file:
                json.dump(server_config, file, indent=2)
            print(f"Generated new server TLS keys in {config_path}")
            return server_config