from rk800.work.base import RK800Cmd, ParseError, CommandStatus
from rk800.context import RK800Context
from rk800.parse import CmdParser, BadArgument, HelpShown


class Result(RK800Cmd):

    def __init__(self, line: str, ctx: RK800Context):
        super().__init__(line, ctx)
        self.target_id = None

    def parse(self):
        parts = self.line.strip().split()[1:]

        try:
            parser = CmdParser(description="Show command results")
            parser.view = self.ctx.view
            parser.add_argument(
                "-i",
                "--id",
                type=int,
                required=True,
                help="Command ID to show result for",
            )

            args = parser.parse_args(parts)
            self.target_id = args.id
        except (BadArgument, HelpShown) as e:
            raise ParseError(f"Invalid result command syntax: {e}")

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
                print(f"  {output}")
        else:
            self.ctx.view.info("No output")
