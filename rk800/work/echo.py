from rk800.work.base import RK800Cmd, ParseError, CommandStatus, CommandResults
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.command_types import Opcode


class Echo(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.message = ""
        self.opcode = Opcode.ECHO

    def parse(self):
        parts = self.line.strip().split(" ", 1)
        if len(parts) < 2 or parts[0].lower() != "echo":
            raise ParseError(f"Invalid echo command: {self.line}")

        self.message = parts[1]
        self.parsed = True

    def execute(self):
        if not self.parsed:
            raise RuntimeError("Command not parsed")
        
        pkt = Packet()
        pkt.set_data(self.opcode, self.message.encode("utf-8") + b'\0')
        
        pkt.send(self.ctx.current_client)
        recv_pkt = Packet()
        recv_pkt.recv(self.ctx.current_client)
        recv_message = recv_pkt.data.rstrip(b'\0').decode("utf-8")
        
        self.output_cache.append(f"sent: {self.message}")
        self.output_cache.append(f"recv: {recv_message}")

        self.status = CommandStatus.FINISHED
        self.result = CommandResults.SUCCESS
