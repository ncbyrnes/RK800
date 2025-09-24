import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Union


class Opcode(IntEnum):
    CLIENT_READY = 101
    SERVER_FIN = 102
    END_DATA = 103
    
    LS = 201
    
    ERROR = 901
    ERRNO_ERROR = 902


@dataclass
class Command:
    payload: Dict[str, Union[str, int, float, bool]]
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
