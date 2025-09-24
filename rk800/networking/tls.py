import ssl
import socket
import select
import tempfile
import os
from contextlib import contextmanager
from enum import Enum, auto
from typing import Optional
from rk800.context import RK800Context
from rk800.networking.packet import Packet
from rk800.networking.exceptions import (
    ClientDisconnectedError,
)

# socket settings
SELECT_TIMEOUT = 5.0
SOCKET_TIMEOUT = 3.0
TEMP_FILE_MODE = 0o600
SOCKET_REUSE_ENABLED = 1
SERVER_SOCKET_TIMEOUT = 5.0
ACCEPT_SOCKET_TIMEOUT = 1.0
CLIENT_SOCKET_TIMEOUT = 30.0
ACCEPT_RETRY_DELAY = 0.1
THREAD_JOIN_TIMEOUT = 5.0


class ClientState(Enum):
    AWAITING_REQUEST = auto()


class TLS:
    """core tls functionality"""

    SINGLE_CONNECTION_BACKLOG = 1

    def __init__(self, address: str, port: int, ctx: RK800Context):
        self.ctx = ctx
        self.address = address
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.is_running = False

        self.server_cert = ""
        self.server_key = ""
        self.ca_cert = ""
        self.temp_files = []

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

            try:
                socket.inet_pton(socket.AF_INET6, self.address)
                family = socket.AF_INET6
            except socket.error:
                family = socket.AF_INET
            
            self.server_socket = socket.socket(family, socket.SOCK_STREAM)
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, SOCKET_REUSE_ENABLED
            )
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

