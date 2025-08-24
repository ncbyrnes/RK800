#!/usr/bin/env python3

import cmd
import argparse
from pathlib import Path
from importlib.resources import files
from rk800.tls_cert import CertManager


class RK800CLI(cmd.Cmd):
    intro = "RK800 CLI. Type help or ? to list commands.\n"
    prompt = "rk800> "

    def do_exit(self, arg):
        """Exit CLI"""
        print("Goodbye")
        return True


class Configure:
    DAEMON_CANARY = b"\x41\x39\x31\x54\x21\xff\x3d\xc1\x7a\x45\x1b\x4e\x31\x5d\x36\xc1"
    DAEMON_FORMAT = "!QQQ256s1024s1024s"
    SEC_IN_MIN = 60

    def __init__(self, binary_path: Path):
        self.binary_path = binary_path
        self.cert_manager = CertManager()

    def _pack_daemon_config(self, args: argparse.Namespace) -> bytes:
        import struct

        beacon_interval_seconds = args.beacon_interval * self.SEC_IN_MIN
        beacon_jitter_seconds = args.beacon_jitter * self.SEC_IN_MIN

        client_certs = self.cert_manager.generate_client_cert()

        return struct.pack(
            self.DAEMON_FORMAT,
            beacon_interval_seconds,
            beacon_jitter_seconds,
            args.connection_weight,
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
            canary_index = data.find(self.DAEMON_CANARY)
            if canary_index != -1:
                packed_config = self._pack_daemon_config(args)
                data[canary_index : canary_index + len(packed_config)] = packed_config

        with open(output_path, "wb") as output_file:
            output_file.write(data)

        print(f"Binary written to {output_path.absolute()}")

        if args and hasattr(args, "beacon_interval"):
            print(f"Beacon interval: {args.beacon_interval} minutes")
            print(f"Beacon jitter: {args.beacon_jitter} minutes")
            print(f"Connection weight: {args.connection_weight}")


class CommandHandler:
    def __init__(self):
        self.arch_mapping = {
            "arm32": "android_arm32",
            "aarch64": "android_aarch64",
            "linux": "linux_x86_64",
        }

    def _find_binary(self, project: str, arch: str) -> Path:
        assets_dir = files("rk800").joinpath("assets")
        assets_path = Path(assets_dir).resolve()

        pattern = f"{project}_*{arch}*.bin"
        matches = list(assets_path.glob(pattern))

        if matches:
            return matches[0]
        raise FileNotFoundError(f"No binary found matching {pattern}")

    def configure(self, args: argparse.Namespace) -> None:
        target_arch = self.arch_mapping[args.arch]
        binary_path = self._find_binary(args.project, target_arch)
        output_path = Path.cwd() / binary_path.name

        configurator = Configure(binary_path)
        configurator.write_configured_binary(output_path, args)

    def listen(self, args: argparse.Namespace) -> None:
        print(f"Starting listener on {args.listen_addr}:{args.listen_port}")
        RK800CLI().cmdloop()

    def dispatch_command(self, args) -> None:
        if args.command == "configure":
            self.configure(args)
        elif args.command == "listen":
            self.listen(args)
        else:
            raise ValueError("No command specified. Use --help for usage.")
