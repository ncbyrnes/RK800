from rk800.work.base import RK800Cmd, ParseError, CommandStatus, CommandResults
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.command_types import Opcode
from rk800.work.error import handle_error_packet
from pathlib import Path


class Put(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.local_path = ""
        self.remote_path = ""
        self.opcode = Opcode.PUT
        self.message = ""

    def parse(self):
        parts = self.line.strip().split()
        if len(parts) < 2 or parts[0].lower() != "put":
            raise ParseError(f"Invalid put command: {self.line}")

        self.local_path = parts[1]
        
        if len(parts) >= 3:
            self.remote_path = parts[2]
        else:
            self.remote_path = Path(self.local_path).name
            
        self.parsed = True

    def execute(self):
        if not self.parsed:
            raise RuntimeError("Command not parsed")
        
        local_file = Path(self.local_path)
        if not local_file.exists():
            self.output_cache.append(f"Local file does not exist: {self.local_path}")
            self.result = CommandResults.ERROR
            self.status = CommandStatus.FINISHED
            return
        
        if not local_file.is_file():
            self.output_cache.append(f"Path is not a file: {self.local_path}")
            self.result = CommandResults.ERROR
            self.status = CommandStatus.FINISHED
            return

        pkt = Packet()
        pkt.set_data(self.opcode, self.remote_path.encode("utf-8") + b'\0')
        pkt.send(self.ctx.current_client)
        
        try:
            with local_file.open('rb') as input_file:
                chunk_size = 4096
                while True:
                    chunk = input_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    data_pkt = Packet()
                    data_pkt.set_data(Opcode.PUT_DATA, chunk)
                    data_pkt.send(self.ctx.current_client)
                
                end_pkt = Packet()
                end_pkt.set_data(Opcode.END_DATA, b'')
                end_pkt.send(self.ctx.current_client)
                
                recv_pkt = Packet()
                recv_pkt.recv(self.ctx.current_client)
                
                error_msg, should_break = handle_error_packet(recv_pkt)
                if error_msg:
                    self.output_cache.append(error_msg)
                    self.result = CommandResults.ERROR
                elif recv_pkt.opcode == Opcode.COMMAND_COMPLETE:
                    self.result = CommandResults.SUCCESS
                    self.output_cache.append(f"Uploaded {self.local_path} to {self.remote_path}")
                else:
                    self.output_cache.append(f"Unexpected opcode: {recv_pkt.opcode}")
                    self.result = CommandResults.ERROR
                        
        except IOError as error:
            self.output_cache.append(f"Failed to read file: {error}")
            self.result = CommandResults.ERROR

        self.status = CommandStatus.FINISHED