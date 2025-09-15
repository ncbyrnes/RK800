import ssl
import socket
import select
import threading
import queue
import tempfile
import os
from contextlib import contextmanager
from enum import Enum, auto
from typing import Optional
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.networking.exceptions import (
    ClientDisconnectedError,
    PacketHandlingError,
    TLSError,
    ServerError,
    ResourceError,
)
from rk800.command_types import Opcode

# socket settings
SELECT_TIMEOUT = 0.1
SOCKET_TIMEOUT = 3.0
TEMP_FILE_MODE = 0o600


class ClientState(Enum):
    AWAITING_REQUEST = auto()


class ClientHandler:
    """Handles individual client connections and packet processing"""

    def __init__(self, ctx: RK800Context):
        self.ctx = ctx

    def handle_client_session(self, ssl_socket, stop_event: threading.Event) -> None:
        """Handle a complete client session until disconnection"""
        while not stop_event.is_set():
            packet = self._receive_packet_with_timeout(ssl_socket)
            if packet and packet.opcode == Opcode.REQUEST_COMMAND:
                self._process_command_request(ssl_socket)

    def _receive_packet_with_timeout(self, ssl_socket) -> Optional[Packet]:
        """Receive a packet with timeout, returning None if no packet available"""
        ready, _, _ = select.select([ssl_socket], [], [], SELECT_TIMEOUT)
        if ready:
            packet = Packet()
            if packet.recv(ssl_socket):
                return packet
        return None

    def _process_command_request(self, ssl_socket) -> None:
        """Process a command request from client"""
        with self.ctx.queue_lock:
            try:
                packet_to_send = self.ctx.send_queue.get_nowait()
                packet_to_send.send(ssl_socket)
            except queue.Empty:
                self._send_no_commands_available(ssl_socket)

    def _send_no_commands_available(self, ssl_socket) -> None:
        """Send NO_COMMANDS_AVAILABLE response to client"""
        packet = Packet()
        packet.set_data(Opcode.NO_COMMANDS_AVAILABLE)
        packet.send(ssl_socket)


class Tls:
    """TLS server for handling client connections"""

    SINGLE_CONNECTION_BACKLOG = 1

    def __init__(self, address: str, port: int, ctx: RK800Context):
        self.ctx = ctx
        self.address = address
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        self.server_cert = ""
        self.server_key = ""
        self.ca_cert = ""
        self.temp_files = []
        self.client_handler = ClientHandler(ctx)

    def _write_temp_file(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.chmod(path, TEMP_FILE_MODE)
            self.temp_files.append(path)
            return path
        except:
            try:
                os.close(fd)
                os.unlink(path)
            except:
                pass
            raise

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for mutual TLS authentication

        Returns:
            ssl.SSLContext: configured SSL context
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        if not self.server_cert or not self.server_key:
            raise ValueError("Server certificate and key must be provided")

        try:
            cert_path = self._write_temp_file(self.server_cert, ".crt")
            key_path = self._write_temp_file(self.server_key, ".key")
            context.load_cert_chain(cert_path, key_path)
        except (ssl.SSLError, ValueError) as error:
            raise ssl.SSLError(f"Failed to load certificate chain: {error}")

        if self.ca_cert:
            try:
                ca_path = self._write_temp_file(self.ca_cert, ".crt")
                context.load_verify_locations(ca_path)
            except (ssl.SSLError, ValueError) as error:
                raise ssl.SSLError(f"Failed to load CA certificate: {error}")

        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False

        cipher_suites = "ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA"
        context.set_ciphers(cipher_suites)

        return context

    def start(self) -> bool:
        """Start the TLS server

        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            self.ssl_context = self._create_ssl_context()

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_REUSE_ENABLED)
            self.server_socket.settimeout(SERVER_SOCKET_TIMEOUT)

            self.server_socket.bind((self.address, self.port))
            self.server_socket.listen(self.SINGLE_CONNECTION_BACKLOG)

            self.is_running = True
            self.ctx.view.success(f"TLS server started on {self.address}:{self.port}")

            return True

        except Exception as error:
            self.ctx.view.error(f"Failed to start TLS server: {error}")
            self.stop()
            return False

    def accept(self) -> Optional[ssl.SSLSocket]:
        """Accept a single TLS connection

        Returns:
            ssl.SSLSocket: SSL socket for client connection, None if failed
        """
        if not self.is_running or not self.server_socket:
            return None

        try:
            self.server_socket.settimeout(ACCEPT_SOCKET_TIMEOUT)
            client_socket, client_addr = self.server_socket.accept()
        except socket.timeout:
            return None

        ssl_socket = None
        try:
            ssl_socket = self.ssl_context.wrap_socket(
                client_socket, server_side=True, do_handshake_on_connect=True
            )
            ssl_socket.settimeout(CLIENT_SOCKET_TIMEOUT)

            client_cert = ssl_socket.getpeercert()
            if not client_cert:
                self.ctx.view.warning(f"Client {client_addr} provided no certificate")
                ssl_socket.close()
                return None

            self.ctx.view.success(f"Accepted TLS connection from {client_addr}")
            return ssl_socket

        except ssl.SSLError as ssl_error:
            self.ctx.view.error(f"SSL handshake failed: {ssl_error}")
            if ssl_socket:
                try:
                    ssl_socket.close()
                except (OSError, ssl.SSLError):
                    pass
            return None
        except (OSError, socket.error) as error:
            self.ctx.view.error(f"Socket error accepting connection: {error}")
            if ssl_socket:
                try:
                    ssl_socket.close()
                except (OSError, ssl.SSLError):
                    pass
            return None
        except Exception as error:
            self.ctx.view.error(f"Unexpected error accepting connection: {error}")
            if ssl_socket:
                try:
                    ssl_socket.close()
                except (OSError, ssl.SSLError):
                    pass
            return None

    def stop(self):
        """Stop the TLS server"""
        self.is_running = False

        if self.server_socket:
            try:
                self.server_socket.close()
            except (OSError, BrokenPipeError):
                pass
            except Exception as error:
                self.ctx.view.warning(f"Error closing server socket: {error}")

        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except (OSError, FileNotFoundError):
                pass
        self.temp_files.clear()

        self.ctx.view.info("TLS server stopped")

    def receive_packet_with_timeout(
        self, ssl_socket, timeout: float = SELECT_TIMEOUT
    ) -> Optional[Packet]:
        ready, _, _ = select.select([ssl_socket], [], [], timeout)
        if ready:
            packet = Packet()
            try:
                if packet.recv(ssl_socket):
                    return packet
                else:
                    raise ClientDisconnectedError(
                        "Client closed connection during receive"
                    )
            except (
                ConnectionResetError,
                ssl.SSLError,
                socket.error,
                ValueError,
            ) as error:
                raise ClientDisconnectedError(
                    f"Client disconnected: {error}"
                ) from error
        return None

    def send_packet(self, ssl_socket, opcode: int, data: bytes = b"") -> None:
        packet = Packet()
        packet.set_data(opcode, data)
        try:
            if not packet.send(ssl_socket):
                raise ClientDisconnectedError("Client closed connection during send")
        except (ConnectionResetError, ssl.SSLError, socket.error, ValueError) as error:
            raise ClientDisconnectedError(f"Failed to send packet: {error}") from error

    @contextmanager
    def _ssl_socket_context(self, ssl_socket):
        """Context manager for proper SSL socket cleanup"""
        try:
            yield ssl_socket
        finally:
            if ssl_socket:
                try:
                    ssl_socket.shutdown(socket.SHUT_RDWR)
                except (OSError, ssl.SSLError):
                    pass
                finally:
                    try:
                        ssl_socket.close()
                    except Exception:
                        pass

    def handle_client(self, ssl_socket) -> None:
        self.client_handler.handle_client_session(ssl_socket, self.stop_event)


    def start_threaded(self):
        if self.is_running:
            return False

        if not self.start():
            return False

        self.stop_event.clear()
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        return True

    def _server_loop(self):
        try:
            while not self.stop_event.is_set():
                ssl_socket = self.accept()
                if not ssl_socket:
                    if not self.stop_event.is_set():
                        self.stop_event.wait(ACCEPT_RETRY_DELAY)
                    continue

                client_addr = ssl_socket.getpeername() if ssl_socket else "unknown"
                self.ctx.view.success(f"Client connected from {client_addr}")

                with self._ssl_socket_context(ssl_socket):
                    try:
                        self.handle_client(ssl_socket)
                    except ClientDisconnectedError as error:
                        self.ctx.view.warning(f"Client disconnected: {error}")
                        break
                    except PacketHandlingError as error:
                        self.ctx.view.error(f"Client error: {error}")
                        break

                self.ctx.view.warning(f"Client disconnected from {client_addr}")

        except Exception as error:
            self.ctx.view.error(f"Error in server loop: {error}")
        finally:
            self.stop()

    def stop_threaded(self):
        if not self.is_running:
            return

        self.ctx.view.info("Stopping threaded TLS server...")
        self.stop_event.set()

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=THREAD_JOIN_TIMEOUT)
            if self.server_thread.is_alive():
                self.ctx.view.warning("Server thread did not stop gracefully")

        self.ctx.view.info("Threaded TLS server stopped")
