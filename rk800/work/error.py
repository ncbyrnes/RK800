from rk800.command_types import Opcode
import struct
import os
from enum import IntEnum


class ErrorCode(IntEnum):
    GENERIC_ERROR = 1
    BAD_PACKET = 2
    EMPTY_FILE = 3


def handle_error_packet(recv_pkt):
    """Handle error packets (opcodes 901 and 902)
    
    Args:
        recv_pkt: Received packet with error opcode
        
    Returns:
        tuple: (error_message, should_break)
    """
    if recv_pkt.opcode == Opcode.ERROR:
        error_code, = struct.unpack("!h", recv_pkt.data[:2])
        try:
            error_name = ErrorCode(error_code).name
            return f"Error: {error_name}", True
        except ValueError:
            return f"Error: Unknown error code {error_code}", True
    elif recv_pkt.opcode == Opcode.ERRNO_ERROR:
        errno_code, = struct.unpack("!h", recv_pkt.data[:2])
        error_msg = os.strerror(errno_code) if hasattr(os, 'strerror') else f"errno {errno_code}"
        return f"System error: {error_msg}", True
    
    return None, False