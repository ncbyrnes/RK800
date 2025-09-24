import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Union


class Opcode(IntEnum):
    CLIENT_READY = 101
    SERVER_FIN = 102
    
    ECHO = 201
    
    ERROR = 900


@dataclass
class Command:
    payload: Dict[str, Union[str, int, float, bool]]
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
