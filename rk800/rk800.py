#!/usr/bin/env python3

import logging
from rk800.parse import parse_args
from rk800.command import CommandHandler

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run():
    """Main entry point for RK800 CLI application
    
    Parses arguments, dispatches commands, and handles exceptions.
    """
    try:
        args = parse_args()
        
        if hasattr(args, 'debug') and args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        
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
