from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
import threading
from rk800.context import RK800Context


class ParseError(Exception):
    """Raised when command parsing fails"""

    pass


class CommandStatus(Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN PROGRESS"
    FINISHED = "FINISHED"
    EXCEPTION = "EXCEPTION"


class CommandResults(Enum):
    NONE = "NONE"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class RK800Cmd(ABC):
    """Base class for RK800 commands"""

    _next_id = 1

    def __init__(self, line: str, ctx: RK800Context):
        with ctx.commands_lock:
            self.id = RK800Cmd._next_id
            RK800Cmd._next_id += 1
        self.line = line
        self.ctx = ctx
        self.parsed = False
        self.status = CommandStatus.QUEUED
        self.result = CommandResults.NONE
        self.output_cache = []

    @abstractmethod
    def parse(self):
        """Parse and validate the command line. Raise ParseError if invalid."""
        raise NotImplementedError

    @abstractmethod
    def execute(self) -> None:
        """Execute the command"""
        raise NotImplementedError
