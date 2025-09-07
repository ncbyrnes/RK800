#!/usr/bin/env python3

import cmd
import argparse
import logging
from pathlib import Path
from rk800.configure import Configure

logger = logging.getLogger(__name__)


class RK800CLI(cmd.Cmd):
    intro = "RK800 CLI. Type help or ? to list commands.\n"
    prompt = "rk800> "

    def do_exit(self, arg):
        """Exit CLI"""
        logger.info("Goodbye")
        return True


class CommandHandler:
    def __init__(self):
        pass

    def configure(self, args: argparse.Namespace) -> None:
        logger.info(f"Configure called with args: {args}")
        output_path = Path.cwd() / args.output if hasattr(args, 'output') and args.output else Path.cwd() / "configured.apk"
        logger.info(f"Output path: {output_path}")
        config = Configure(output_path, args)
        config.write_configured_apk()

    def listen(self, args: argparse.Namespace) -> None:
        logger.info(f"Starting listener on {args.listen_addr}:{args.listen_port}")
        RK800CLI().cmdloop()

    def dispatch_command(self, args) -> None:
        if args.command == "config":
            self.configure(args)
        elif args.command == "listen":
            self.listen(args)
        else:
            raise ValueError("No command specified. Use --help for usage.")
