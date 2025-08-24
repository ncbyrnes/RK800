#!/usr/bin/env python3

from rk800.parse import parse_args
from rk800.command import CommandHandler


def run():
    try:
        args = parse_args()
        handler = CommandHandler()
        handler.dispatch_command(args)

    except KeyboardInterrupt:
        print("\nInterrupted")
    except FileNotFoundError as error:
        print(f"File not found: {error}")
    except ValueError as error:
        print(f"Invalid argument: {error}")
    except OSError as error:
        print(f"System error: {error}")
