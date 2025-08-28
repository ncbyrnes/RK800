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

    # configure
    configure_parser = subparsers.add_parser("configure", help="configure RK800")
    configure_parser.add_argument(
        "arch", choices=["arm32", "aarch64"], help="target architecture"
    )

    configure_subparsers = configure_parser.add_subparsers(
        dest="project", help="project to configure"
    )

    # loader
    loader_parser = configure_subparsers.add_parser("loader", help="configure loader")

    # daemon
    daemon_parser = configure_subparsers.add_parser("daemon", help="configure daemon")
    daemon_parser.add_argument(
        "-i",
        "--beacon-interval",
        type=int,
        default=120,
        help="beacon interval in minutes, default: 120",
    )
    daemon_parser.add_argument(
        "-j",
        "--beacon-jitter",
        type=int,
        default=60,
        help="beacon jitter in minutes, default: 60",
    )
    daemon_parser.add_argument(
        "-w",
        "--connection-weight",
        type=int,
        default=0,
        help="commands per connection, default: 0 (no limit)",
    )
    daemon_parser.add_argument("-a", "--address", type=str, required=True, help="REQUIRED: callback address")
    daemon_parser.add_argument("-p", "--port", type=int, required=True, help="REQUIRED: callback port")

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
