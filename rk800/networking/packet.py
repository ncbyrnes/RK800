import ssl
import socket
import struct

PACKET_HEADER_SIZE = 4
OPCODE_SIZE = 2
PACKET_LENGTH_SIZE = 2
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
        """
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionResetError(
                    f"Connection closed while receiving data (got {len(data)}/{size} bytes)"
                )
            data += chunk
        return data

    def recv(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Receive packet from socket

        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to receive from

        Returns:
            bool: True if packet received successfully, False otherwise

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

            return True

        except (ssl.SSLError, socket.timeout, OSError, ConnectionResetError) as error:
            raise type(error)(f"Error receiving packet: {error}") from error

    def send(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Send packet to socket

        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to send to

        Returns:
            bool: True if packet sent successfully, False otherwise

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

        try:
            header = struct.pack("!HH", self.opcode, self.packet_len)
            packet_data = header + self.data

            total_sent = 0
            while total_sent < len(packet_data):
                bytes_sent = ssl_socket.send(packet_data[total_sent:])
                if bytes_sent == 0:
                    raise ConnectionResetError("Connection closed while sending packet")
                total_sent += bytes_sent
            return True
        except (ssl.SSLError, socket.timeout, OSError) as error:
            raise type(error)(f"Error sending packet: {error}") from error
