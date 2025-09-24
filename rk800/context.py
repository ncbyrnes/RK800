import threading
import uuid
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rk800.work.base import RK800Cmd, CommandStatus
from rk800.view import ViewManager


class RK800Context:
    """Shared context for RK800 application state - manages view and mutex queues"""

    MAX_COMMANDS = 1000

    def __init__(self) -> None:
        self.view: ViewManager = ViewManager()
        self.commands_lock: threading.Lock = threading.Lock()
        self.commands: List["RK800Cmd"] = []
        self.current_client = None


    def add_command(self, command: "RK800Cmd") -> None:
        """Add a command to the tracking list

        Args:
            command: RK800Cmd instance
        """
        with self.commands_lock:
            self.commands.append(command)
            if len(self.commands) > self.MAX_COMMANDS:
                self.commands.pop(0)

    def get_commands(self) -> List["RK800Cmd"]:
        with self.commands_lock:
            return self.commands

    def get_next_queued(self) -> Optional["RK800Cmd"]:
        from rk800.work.base import CommandStatus
        with self.commands_lock:
            for cmd in self.commands:
                if cmd.status == CommandStatus.QUEUED:
                    return cmd
            return None
