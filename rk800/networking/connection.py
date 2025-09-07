import logging
from typing import Optional
from rk800.networking.tls import Tls, Packet

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Simple connection manager for single TLS connections"""
    
    def __init__(self, address: str = "0.0.0.0", port: int = 443):
        """Initialize connection manager
        
        Args:
            address (str): bind address for server
            port (int): bind port for server
        """
        self.tls = Tls(address, port)
        self.ssl_socket: Optional = None
        
    def start(self) -> bool:
        """Start the connection server
        
        Returns:
            bool: True if server started successfully, False otherwise
        """
        return self.tls.start()
    
    def accept_connection(self):
        """Accept a client connection
        
        Returns:
            bool: True if connection accepted successfully, False otherwise
        """
        self.ssl_socket = self.tls.accept()
        return self.ssl_socket is not None
    
    def send_packet(self, packet: Packet) -> bool:
        """Send packet to connected client
        
        Args:
            packet (Packet): packet to send
            
        Returns:
            bool: True if packet sent successfully, False otherwise
        """
        if not self.ssl_socket:
            return False
        return packet.send(self.ssl_socket)
    
    def recv_packet(self, packet: Packet) -> bool:
        """Receive packet from connected client
        
        Args:
            packet (Packet): packet object to fill with received data
            
        Returns:
            bool: True if packet received successfully, False otherwise
        """
        if not self.ssl_socket:
            return False
        return packet.recv(self.ssl_socket)
    
    def close_connection(self):
        """Close the current connection"""
        if self.ssl_socket:
            try:
                self.ssl_socket.close()
            except Exception as error:
                logger.warning(f"Error closing SSL connection: {error}")
            finally:
                self.ssl_socket = None
    
    def stop(self):
        """Stop the connection manager"""
        self.close_connection()
        self.tls.stop()