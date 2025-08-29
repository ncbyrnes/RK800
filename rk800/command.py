#!/usr/bin/env python3

import cmd
import argparse
from pathlib import Path
from importlib.resources import files
from rk800.configure import Configure


class RK800CLI(cmd.Cmd):
    intro = "RK800 CLI. Type help or ? to list commands.\n"
    prompt = "rk800> "

    def do_exit(self, arg):
        """Exit CLI"""
        print("Goodbye")
        return True


class CommandHandler:
    def __init__(self):
        self.arch_mapping = {
            "arm32": "android_arm32",
            "aarch64": "android_aarch64",
        }

    def _find_binary(self, arch: str) -> Path:
        assets_dir = files("rk800").joinpath("assets")
        assets_path = Path(assets_dir).resolve()

        pattern = f"daemon_*{arch}*.so"
        matches = list(assets_path.glob(pattern))

        if matches:
            return matches[0]
        raise FileNotFoundError(f"No binary found matching {pattern}")

    def configure(self, args: argparse.Namespace) -> None:
        target_arch = self.arch_mapping[args.arch]
        binary_path = self._find_binary(target_arch)
        output_path = Path.cwd() / (args.arch + ".apk")

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
