from rk800.work.base import RK800Cmd, ParseError, CommandStatus, CommandResults
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.command_types import Opcode
from rk800.work.error import handle_error_packet
import struct
import stat


class Ls(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.path = ""
        self.opcode = Opcode.LS
        self.message = ""

    def parse(self):
        parts = self.line.strip().split(" ", 1)
        if len(parts) < 1 or parts[0].lower() != "ls":
            raise ParseError(f"Invalid ls command: {self.line}")

        if len(parts) == 2:
            self.path = parts[1]
        else:
            self.path = "."
            
        self.parsed = True

    def execute(self):
        if not self.parsed:
            raise RuntimeError("Command not parsed")
        
        pkt = Packet()
        pkt.set_data(self.opcode, self.path.encode("utf-8") + b'\0')
        
        pkt.send(self.ctx.current_client)
        
        while True:
            recv_pkt = Packet()
            recv_pkt.recv(self.ctx.current_client)
            
            error_msg, should_break = handle_error_packet(recv_pkt)
            if error_msg:
                self.output_cache.append(error_msg)
                self.result = CommandResults.ERROR
                break
            elif recv_pkt.opcode == Opcode.LS:
                mode, = struct.unpack("!L", recv_pkt.data[:4])
                name = recv_pkt.data[4:].decode("utf-8").rstrip('\0')
                mode_str = stat.filemode(mode)
                self.output_cache.append(f"{mode_str} {name}")
            elif recv_pkt.opcode == Opcode.END_DATA:
                break
            else:
                self.output_cache.append(f"Unexpected opcode: {recv_pkt.opcode}")
                break

        self.status = CommandStatus.FINISHED
        if self.result == CommandResults.NONE:
            self.result = CommandResults.SUCCESS