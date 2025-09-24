from rk800.work.base import RK800Cmd, ParseError, CommandStatus
from rk800.context import RK800Context
from rk800.parse import CmdParser, BadArgument, HelpShown


class Result(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.target_id = None

    def parse(self):
        parts = self.line.strip().split()
        
        if len(parts) < 2 or parts[0] != "result":
            raise ParseError(f"Invalid result command: {self.line}")
        
        try:
            self.target_id = int(parts[1])
        except ValueError:
            raise ParseError(f"Invalid command ID: {parts[1]}")

        self.parsed = True

    def execute(self):
        if not self.parsed:
            raise RuntimeError("Command not parsed")

        commands = self.ctx.get_commands()

        if not commands:
            self.ctx.view.info("No commands in queue")
            return

        for cmd in commands:
            if cmd.id == self.target_id:
                self._display_command_result(cmd)
                return
        self.ctx.view.error(f"Command with ID {self.target_id} not found")

    def _display_command_result(self, cmd):
        self.ctx.view.info(f"Command: {cmd.line}")

        if cmd.output_cache:
            self.ctx.view.info("Output:")
            for output in cmd.output_cache:
                self.ctx.view.info(f"  {output}")
        else:
            self.ctx.view.info("No output")
