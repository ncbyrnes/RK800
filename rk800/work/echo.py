from rk800.work.base import RK800Cmd, ParseError, CommandStatus
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
        """Execute echo command by queueing packet for transmission to client

        Raises:
            RuntimeError: If command has not been parsed before execution
        """
        if not self.parsed:
            raise RuntimeError("Command not parsed")

        packet = Packet()
        packet.set_data(self.opcode, self.message.encode("utf-8"))
        self.ctx.enqueue_packet(packet)
