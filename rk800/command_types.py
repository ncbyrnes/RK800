import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Union


class Opcode(IntEnum):
    ECHO = 1

    REQUEST_COMMAND = 100
    COMMAND_RESULT = 101

    DISPATCH_COMMAND = 200
    NO_COMMANDS_AVAILABLE = 201
    ACKNOWLEDGE_RESULT = 202


@dataclass
class Command:
    payload: Dict[str, Union[str, int, float, bool]]
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
