import ssl
import socket
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PACKET_HEADER_SIZE = 4
OPCODE_SIZE = 2
PACKET_LENGTH_SIZE = 2


class Packet:
    """Packet with 4-byte header protocol
    
    Protocol format:
        - 2 bytes: opcode
        - 2 bytes: packet length (excluding 4-byte header)
        - packet_len bytes: data
    """
    
    def __init__(self):
        self.opcode = 0
        self.packet_len = 0
        self.data = b''
    
    def set_data(self, opcode: int, data: bytes = b''):
        """Set packet opcode and data
        
        Args:
            opcode (int): packet operation code
            data (bytes): packet payload data
        """
        self.opcode = opcode
        self.data = data
        self.packet_len = len(data)
    
    def recv(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Receive packet from socket
        
        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to receive from
            
        Returns:
            bool: True if packet received successfully, False otherwise
        """
        try:
            header_data = b''
            while len(header_data) < PACKET_HEADER_SIZE:
                chunk = ssl_socket.recv(PACKET_HEADER_SIZE - len(header_data))
                if not chunk:
                    return False
                header_data += chunk
            
            self.opcode, self.packet_len = struct.unpack('!HH', header_data)
            
            self.data = b''
            while len(self.data) < self.packet_len:
                chunk = ssl_socket.recv(self.packet_len - len(self.data))
                if not chunk:
                    return False
                self.data += chunk
            
            return True
        
        except Exception as error:
            logger.error(f"Error receiving packet: {error}")
            return False
    
    def send(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Send packet to socket
        
        Args:
            ssl_socket (ssl.SSLSocket): SSL socket to send to
            
        Returns:
            bool: True if packet sent successfully, False otherwise
        """
        try:
            header = struct.pack('!HH', self.opcode, self.packet_len)
            packet_data = header + self.data
            
            total_sent = 0
            while total_sent < len(packet_data):
                bytes_sent = ssl_socket.send(packet_data[total_sent:])
                if bytes_sent == 0:
                    return False
                total_sent += bytes_sent
            return True
        except Exception as error:
            logger.error(f"Error sending packet: {error}")
            return False


class Tls:
    """TLS server for handling client connections"""
    
    DEFAULT_BIND_ADDRESS = "0.0.0.0"
    DEFAULT_PORT = 4444
    SINGLE_CONNECTION_BACKLOG = 1
    
    def __init__(self, address: str = DEFAULT_BIND_ADDRESS, port: int = DEFAULT_PORT):
        """Initialize TLS server
        
        Args:
            address (str): bind address for server
            port (int): bind port for server
        """
        self.address = address
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        self.is_running = False
        
        # TODO: Implement CertManager integration
        self.server_cert = ""
        self.server_key = "" 
        self.ca_cert = ""
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for mutual TLS authentication
        
        Returns:
            ssl.SSLContext: configured SSL context
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        context.load_cert_chain_from_bytes(
            self.server_cert.encode(), 
            self.server_key.encode()
        )
        
        context.load_verify_locations(cadata=self.ca_cert)
        
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False
        
        cipher_suites = 'ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA'
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
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.server_socket.bind((self.address, self.port))
            self.server_socket.listen(self.SINGLE_CONNECTION_BACKLOG)
            
            self.is_running = True
            logger.info(f"TLS server started on {self.address}:{self.port}")
            
            return True
            
        except Exception as error:
            logger.error(f"Failed to start TLS server: {error}")
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
            client_socket, client_addr = self.server_socket.accept()
            
            ssl_socket = self.ssl_context.wrap_socket(
                client_socket,
                server_side=True,
                do_handshake_on_connect=True
            )
            
            client_cert = ssl_socket.getpeercert()
            if not client_cert:
                logger.warning(f"Client {client_addr} provided no certificate")
                ssl_socket.close()
                return None
                
            logger.info(f"Accepted TLS connection from {client_addr}")
            logger.debug(f"Client certificate subject: {client_cert.get('subject')}")
            
            return ssl_socket
            
        except ssl.SSLError as ssl_error:
            logger.error(f"SSL handshake failed: {ssl_error}")
            return None
        except Exception as error:
            logger.error(f"Error accepting connection: {error}")
            return None
    
    def stop(self):
        """Stop the TLS server"""
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as error:
                logger.warning(f"Error closing server socket: {error}")
                
        logger.info("TLS server stopped")