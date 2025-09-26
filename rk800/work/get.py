from rk800.work.base import RK800Cmd, ParseError, CommandStatus, CommandResults
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.command_types import Opcode
from rk800.work.error import handle_error_packet
from pathlib import Path


class Get(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.remote_path = ""
        self.local_path = ""
        self.opcode = Opcode.GET
        self.message = ""

    def parse(self):
        parts = self.line.strip().split()
        if len(parts) < 2 or parts[0].lower() != "get":
            raise ParseError(f"Invalid get command: {self.line}")

        self.remote_path = parts[1]
        
        if len(parts) >= 3:
            self.local_path = parts[2]
        else:
            self.local_path = Path(self.remote_path).name
            
        self.parsed = True

    def execute(self):
        if not self.parsed:
            raise RuntimeError("Command not parsed")
        
        pkt = Packet()
        pkt.set_data(self.opcode, self.remote_path.encode("utf-8") + b'\0')
        
        pkt.send(self.ctx.current_client)
        
        try:
            with Path(self.local_path).open('wb') as output_file:
                while True:
                    recv_pkt = Packet()
                    recv_pkt.recv(self.ctx.current_client)
                    
                    error_msg, should_break = handle_error_packet(recv_pkt)
                    if error_msg:
                        self.output_cache.append(error_msg)
                        self.result = CommandResults.ERROR
                        break
                    elif recv_pkt.opcode == Opcode.GET_DATA:
                        output_file.write(recv_pkt.data)
                    elif recv_pkt.opcode == Opcode.END_DATA:
                        break
                    else:
                        self.output_cache.append(f"Unexpected opcode: {recv_pkt.opcode}")
                        break
                        
        except IOError as error:
            self.output_cache.append(f"Failed to write file: {error}")
            self.result = CommandResults.ERROR

        self.status = CommandStatus.FINISHED
        if self.result == CommandResults.NONE:
            self.result = CommandResults.SUCCESS
            self.output_cache.append(f"Downloaded {self.remote_path} to {self.local_path}")