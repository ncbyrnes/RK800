import ssl
import socket
import struct
from rk800.command_types import Opcode
from rk800.work.error import handle_error_packet

PACKET_HEADER_SIZE = 4
MAX_PACKET_SIZE = 0xFFFF


class Packet:
    """Packet Abstraction"""

    def __init__(self):
        self.opcode = 0
        self.packet_len = 0
        self.data = b""

    def set_data(self, opcode: int, data: bytes = b""):
        """Set packet opcode and data

        Args:
            opcode (int): packet operation code
            data (bytes): packet payload data
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) > MAX_PACKET_SIZE:
            raise ValueError(f"data size {len(data)} exceeds maximum {MAX_PACKET_SIZE}")
        
        self.opcode = opcode
        self.data = data
        self.packet_len = len(data)

    def _recv_all(self, sock: ssl.SSLSocket, size: int) -> bytes:
        """Receive exactly 'size' bytes from socket

        Args:
            sock: SSL socket to receive from
            size: Number of bytes to receive

        Returns:
            bytes: Received data

        Raises:
            ConnectionResetError: If connection is closed before all data received
            ValueError: If size is invalid
        """
        if size < 0:
            raise ValueError("size cannot be negative")
        if size > MAX_PACKET_SIZE:
            raise ValueError(f"size {size} exceeds maximum {MAX_PACKET_SIZE}")
        
        chunks = []
        bytes_received = 0
        while bytes_received < size:
            chunk = sock.recv(size - bytes_received)
            if not chunk:
                raise ConnectionResetError(
                    f"Connection closed while receiving data (got {bytes_received}/{size} bytes)"
                )
            chunks.append(chunk)
            bytes_received += len(chunk)
        return b"".join(chunks)

    def recv(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Receive packet from socket

        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to receive from

        Returns:
            bool: True if packet received successfully, False if error packet

        Raises:
            ValueError: If packet size exceeds maximum allowed
            ssl.SSLError: For SSL-related errors
            socket.error: For socket-related errors
            ConnectionResetError: If connection is reset by peer
        """
        try:
            header_data = self._recv_all(ssl_socket, PACKET_HEADER_SIZE)
            self.opcode, self.packet_len = struct.unpack("!HH", header_data)

            if self.packet_len > MAX_PACKET_SIZE:
                raise ValueError(
                    f"Packet size {self.packet_len} exceeds maximum {MAX_PACKET_SIZE}"
                )

            if self.packet_len > 0:
                self.data = self._recv_all(ssl_socket, self.packet_len)
            else:
                self.data = b""

            if self.opcode == Opcode.ERROR or self.opcode == Opcode.ERRNO_ERROR:
                return False

            return True

        except (ssl.SSLError, socket.timeout, OSError, ConnectionResetError) as error:
            raise type(error)(f"Error receiving packet: {error}") from error

    def get_error_msg(self) -> str:
        """get error message from error packet"""
        error_msg, _ = handle_error_packet(self)
        return error_msg or ""


    def send(self, ssl_socket: ssl.SSLSocket) -> None:
        """Send packet to socket

        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to send to

        Raises:
            ValueError: If packet size exceeds maximum allowed
            ssl.SSLError: For SSL-related errors
            socket.error: For socket-related errors
            ConnectionResetError: If connection is reset by peer
        """
        if self.packet_len > MAX_PACKET_SIZE:
            raise ValueError(
                f"Packet size {self.packet_len} exceeds maximum {MAX_PACKET_SIZE}"
            )

        header = struct.pack("!HH", self.opcode, self.packet_len)
        packet_data = header + self.data

        total_sent = 0
        while total_sent < len(packet_data):
            try:
                bytes_sent = ssl_socket.send(packet_data[total_sent:])
                if bytes_sent == 0:
                    raise ConnectionResetError("Connection closed while sending packet")
                total_sent += bytes_sent
            except (ssl.SSLError, socket.timeout, OSError) as error:
                raise type(error)(f"Error sending packet: {error}") from error
