from rk800.parse import parse_args
from rk800.command import CommandHandler
from rk800.context import RK800Context


def run():
    """Main entry point for RK800 CLI application

    Parses arguments, dispatches commands, and handles exceptions.
    """
    ctx = RK800Context()
    try:
        args = parse_args()

        if hasattr(args, "debug") and args.debug:
            ctx.view.enable_debug()
            ctx.view.debug("Debug enabled")

        handler = CommandHandler(ctx)
        handler.dispatch_command(args)

    except KeyboardInterrupt:
        ctx.view.info("\nInterrupted")
    except FileNotFoundError as error:
        ctx.view.error(f"File not found: {error}")
    except ValueError as error:
        ctx.view.error(f"Invalid argument: {error}")
    except OSError as error:
        ctx.view.error(f"System error: {error}")
