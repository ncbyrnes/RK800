import ssl
import socket
import select
import threading
from typing import Optional
from rk800.context import RK800Context
from rk800.networking.tls import TLS
from rk800.networking.packet import Packet
from rk800.networking.exceptions import ClientDisconnectedError, PacketHandlingError
from rk800.command_types import Opcode
from rk800.work.base import CommandStatus

# socket settings
SELECT_TIMEOUT = 5.0
ACCEPT_RETRY_DELAY = 0.1
THREAD_JOIN_TIMEOUT = 5.0


class ClientHandler:
    """Handles individual client connections and packet processing"""

    def __init__(self, ctx: RK800Context):
        self.ctx = ctx

    def handle_client_session(self, ssl_socket, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            ready, _, _ = select.select([ssl_socket], [], [], SELECT_TIMEOUT)
            if ready:
                packet = Packet()
                try:
                    if packet.recv(ssl_socket):
                        self.ctx.view.debug(f"Received packet: opcode={packet.opcode}, len={packet.packet_len}")
                        if packet.opcode == Opcode.CLIENT_READY:
                            if not self._process_command_request(ssl_socket):
                                break
                    else:
                        self.ctx.view.debug("Client closed connection")
                        break
                except (ConnectionResetError, ssl.SSLError, socket.error) as error:
                    self.ctx.view.debug(f"Client disconnected: {error}")
                    break
            else:
                self.ctx.view.debug("No data ready within timeout")

    def _process_command_request(self, ssl_socket) -> bool:
        cmd = self.ctx.get_next_queued()
        
        if cmd:
            cmd.status = CommandStatus.IN_PROGRESS
            self.ctx.current_client = ssl_socket
            cmd.execute()
            return True
        else:
            self._send_no_commands_available(ssl_socket)
            return True

    def _send_no_commands_available(self, ssl_socket) -> None:
        packet = Packet()
        packet.set_data(Opcode.SERVER_FIN)
        packet.send(ssl_socket)
    
    def _is_client_connected(self, ssl_socket) -> bool:
        try:
            ready, _, _ = select.select([ssl_socket], [], [], 0)
            return not ready
        except (ConnectionResetError, ssl.SSLError, socket.error, OSError):
            return False


class Server:
    """server logic and client handling"""

    def __init__(self, tls: TLS, ctx: RK800Context):
        self.tls = tls
        self.ctx = ctx
        self.client_handler = ClientHandler(ctx)
        self.server_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start_threaded(self):
        if self.tls.is_running:
            return False

        if not self.tls.start():
            return False

        self.stop_event.clear()
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        return True

    def _server_loop(self):
        while not self.stop_event.is_set():
            try:
                ssl_socket = self._wait_for_client()
                if ssl_socket:
                    self._handle_client_session(ssl_socket)
            except Exception as error:
                self.ctx.view.error(f"Error in server loop: {error}")
                continue
        self.tls.stop()

    def _wait_for_client(self):
        ssl_socket = self.tls.accept()
        if not ssl_socket:
            if not self.stop_event.is_set():
                self.stop_event.wait(ACCEPT_RETRY_DELAY)
            return None
        return ssl_socket

    def _handle_client_session(self, ssl_socket):
        client_addr = ssl_socket.getpeername() if ssl_socket else "unknown"
        self.ctx.view.success(f"Client connected from {client_addr}")

        with self.tls._ssl_socket_context(ssl_socket):
            try:
                self.client_handler.handle_client_session(ssl_socket, self.stop_event)
            except ClientDisconnectedError as error:
                self.ctx.view.warning(f"Client disconnected: {error}")
            except PacketHandlingError as error:
                self.ctx.view.error(f"Client error: {error}")

        self.ctx.view.warning(f"Client disconnected from {client_addr}")


    def stop_threaded(self):
        if not self.tls.is_running:
            return

        self.ctx.view.info("Stopping threaded TLS server...")
        self.stop_event.set()

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=THREAD_JOIN_TIMEOUT)
            if self.server_thread.is_alive():
                self.ctx.view.warning("Server thread did not stop gracefully")

        self.ctx.view.info("Threaded TLS server stopped")