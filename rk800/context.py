import threading
import queue
import uuid
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from rk800.work.base import RK800Cmd
from rk800.view import ViewManager
from rk800.networking.packet import Packet


class RK800Context:
    """Shared context for RK800 application state - manages view and mutex queues"""

    MAX_COMMANDS = 1000

    def __init__(self) -> None:
        self.view: ViewManager = ViewManager()
        self.send_queue: queue.Queue[Packet] = queue.Queue()
        self.recv_queue: queue.Queue[Packet] = queue.Queue()
        self.queue_lock: threading.Lock = threading.Lock()
        self.commands: List["RK800Cmd"] = []

    def enqueue_packet(self, packet: Packet) -> None:
        """Enqueue a packet for sending to clients

        Args:
            packet (Packet): packet to send to clients
        """
        with self.queue_lock:
            self.send_queue.put(packet)

    def dequeue_packet(self) -> Packet:
        """Dequeue a packet from the receive queue without blocking

        Returns:
            Packet: The next available packet

        Raises:
            queue.Empty: If the receive queue is empty
        """
        with self.queue_lock:
            return self.recv_queue.get_nowait()

    def add_command(self, command: "RK800Cmd") -> None:
        """Add a command to the tracking list

        Args:
            command: RK800Cmd instance
        """
        with self.queue_lock:
            self.commands.append(command)
            if len(self.commands) > self.MAX_COMMANDS:
                self.commands.pop(0)

    def get_commands(self) -> List["RK800Cmd"]:
        """Get a copy of all tracked commands

        Returns:
            List of RK800Cmd instances
        """
        with self.queue_lock:
            return self.commands.copy()
