#!/usr/bin/env python3

import logging
from rk800.parse import parse_args
from rk800.command import CommandHandler

logger = logging.getLogger(__name__)


def run():
    try:
        args = parse_args()
        handler = CommandHandler()
        handler.dispatch_command(args)

    except KeyboardInterrupt:
        logger.info("\nInterrupted")
    except FileNotFoundError as error:
        logger.error(f"File not found: {error}")
    except ValueError as error:
        logger.error(f"Invalid argument: {error}")
    except OSError as error:
        logger.error(f"System error: {error}")
