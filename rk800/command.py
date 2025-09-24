import cmd
import argparse
import threading
import asyncio
import queue
import shlex
from pathlib import Path
from typing import Optional, List, Generator
from rk800.configure import Configure
from rk800.networking.tls import TLS
from rk800.networking.server import Server
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.completion.base import CompleteEvent
from prompt_toolkit.formatted_text import FormattedText
from tabulate import tabulate
from rk800.context import RK800Context
from rk800.work.echo import Echo
from rk800.work.base import ParseError


class CLICommandProcessor:
    """Processes commands for the interactive CLI"""

    def __init__(self, ctx: RK800Context):
        self.ctx = ctx
        self.command_handlers = {
            "exit": self._handle_exit,
            "help": self._handle_help,
            "clear": self._handle_clear,
            "queue": self._handle_queue,
            "echo": self._handle_echo,
            "result": self._handle_result,
        }

    def process_command(self, command: str) -> bool:
        """Process a command and return whether to continue running"""
        command = command.strip()
        if not command:
            return True

        try:
            parts = shlex.split(command)
            if not parts:
                return True
            
            cmd_name = parts[0]
            
            if cmd_name in self.command_handlers:
                return self.command_handlers[cmd_name](command)
            else:
                self.ctx.view.error(
                    f"Unknown command: '{cmd_name}'. Type 'help' for available commands."
                )
                return True
        except ValueError as error:
            self.ctx.view.error(f"Invalid command syntax: {error}")
            return True

    def _handle_exit(self, command: str = "") -> bool:
        self.ctx.view.info("Goodbye")
        return False

    def _handle_help(self, command: str = "") -> bool:
        self.ctx.view.info("Available commands:")
        self.ctx.view.info("  exit       - Exit the CLI")
        self.ctx.view.info("  help       - Show this help")
        self.ctx.view.info("  clear      - Clear the screen")
        self.ctx.view.info("  echo <msg> - Queue echo command to send to clients")
        self.ctx.view.info("  queue      - Show queued commands and their status")
        self.ctx.view.info(
            "  result     - Show command results (use -i <id> for specific command)"
        )
        return True

    def _handle_clear(self, command: str = "") -> bool:
        self.ctx.view.clear_screen()
        return True

    def _handle_echo(self, command: str) -> bool:
        try:
            echo_cmd = Echo(command, self.ctx)
            echo_cmd.parse()
            self.ctx.add_command(echo_cmd)
            self.ctx.view.success(
                f"Echo command queued: {echo_cmd.message} (ID: {echo_cmd.id})"
            )
        except ParseError as error:
            self.ctx.view.error(f"Parse error: {error}")
        except Exception as error:
            self.ctx.view.error(f"Failed to queue echo command: {error}")
        return True

    def _handle_queue(self, command: str = "") -> bool:
        try:
            commands = self.ctx.get_commands()

            if not commands:
                self.ctx.view.info("No commands in queue")
                return True

            table_data = []
            for cmd in commands:
                table_data.append(
                    [cmd.id, cmd.line, cmd.status.value, cmd.result.value]
                )

            headers = ["ID", "Command", "Status", "Result"]
            table = tabulate(
                table_data, headers=headers, tablefmt="simple", numalign="left"
            )
            self.ctx.view.info(table)

        except Exception as error:  # python warcrime but idc for something experimental
            self.ctx.view.error(f"Failed to display queue: {error}")
        return True

    def _handle_result(self, command: str) -> bool:
        try:
            from rk800.work.result import Result

            result_cmd = Result(command, self.ctx)
            result_cmd.parse()
            result_cmd.execute()
        except ParseError as error:
            self.ctx.view.error(f"Parse error: {error}")
        except Exception as error:
            self.ctx.view.error(f"Failed to execute result command: {error}")
        return True


class FirstWordCompleter(Completer):
    """Auto-completer that suggests commands based on first word input.

    Args:
        commands: List of command strings to offer as completions
    """

    def __init__(self, commands: List[str]) -> None:
        self.commands = commands

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Generator[Completion, None, None]:
        text = document.text_before_cursor
        if " " not in text:
            for command in self.commands:
                if command.startswith(text.lower()):
                    yield Completion(command, start_position=-len(text))


class RK800CLI:
    """Interactive CLI interface for RK800 with async prompt toolkit"""

    def __init__(self, ctx: RK800Context, server: Optional[Server] = None) -> None:
        self.ctx = ctx
        self.server = server
        self.processor = CLICommandProcessor(ctx)
        self.commands: List[str] = ["exit", "help", "clear", "echo", "queue", "result"]
        self.completer = FirstWordCompleter(self.commands)
        self.session = PromptSession(completer=self.completer)
        self.running = True

    async def run(self) -> None:
        self._display_welcome_message()

        while self._should_continue():
            try:
                user_input = await self._get_user_input()
                self.running = self.processor.process_command(user_input)
            except (KeyboardInterrupt, EOFError):
                break

        self._cleanup_server()

    def _display_welcome_message(self) -> None:
        self.ctx.view.info("RK800 CLI. Type 'help' for commands or 'exit' to quit.")
        self.ctx.view.info("Press TAB for command completion.")

    def _should_continue(self) -> bool:
        return self.running and (not self.server or self.server.tls.is_running)

    async def _get_user_input(self) -> str:
        prompt_text = FormattedText(self.ctx.view.get_prompt_style())
        user_input = await self.session.prompt_async(
            prompt_text, style=self.ctx.view.style
        )
        return user_input.strip()

    def _cleanup_server(self) -> None:
        if self.server:
            self.server.stop_threaded()


class CommandHandler:
    """Handle command dispatch for RK800 operations"""

    def __init__(self, ctx: RK800Context) -> None:
        self.ctx = ctx
        self.command_registry = {"config": self.configure, "listen": self.listen}

    def configure(self, args: argparse.Namespace) -> None:
        self.ctx.view.debug(f"Configure called with args: {args}")
        output_path = (
            Path.cwd() / args.output
            if hasattr(args, "output") and args.output
            else Path.cwd() / "configured.apk"
        )
        self.ctx.view.debug(f"Output path: {output_path}")
        config = Configure(output_path, args, self.ctx)
        config.write_configured_apk()

    def listen(self, args: argparse.Namespace) -> None:
        try:
            from rk800.tls_cert import RK800CertStore

            tls = TLS(args.listen_addr, args.listen_port, self.ctx)

            cert_manager = RK800CertStore(self.ctx)
            tls_config = cert_manager.get_server_tls_config()
            tls.server_cert = tls_config["server_cert"]
            tls.server_key = tls_config["server_key"]
            tls.ca_cert = tls_config["ca_cert"]

            server = Server(tls, self.ctx)
            server.start_threaded()

            cli = RK800CLI(self.ctx, server)
            asyncio.run(cli.run())

        except KeyboardInterrupt:
            self.ctx.view.info("\nShutting down server...")
        except Exception as error:
            self.ctx.view.error(f"Server error: {error}")
        finally:
            if "server" in locals():
                server.stop_threaded()

    def dispatch_command(self, args: argparse.Namespace) -> None:
        command_func = self.command_registry.get(args.command)
        if not command_func:
            available_commands = ", ".join(self.command_registry.keys())
            raise ValueError(
                f"Unknown command '{args.command}'. Available commands: {available_commands}"
            )
        command_func(args)
