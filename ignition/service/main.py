from typing import *
from ..common.communicator import Communicator
import socket
import asyncio
from uuid import uuid4
from functools import partial


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class QueuedPool:
    start_port: int
    end_port: int
    size: int
    loop: asyncio.AbstractEventLoop

    unused_ports: Set[int]
    unused_ids: Set[str]
    queue: List[asyncio.Future, Callable[[Tuple[str, int]], Awaitable[str]]]
    pending: Set[asyncio.Task]

    def __init__(self, start_port: int, end_port: Optional[int], loop: Optional[asyncio.AbstractEventLoop]) -> None:
        self.start_port = start_port
        self.end_port = end_port if end_port else start_port
        self.size = self.end_port - self.start_port + 1
        self.loop = loop if loop else asyncio.get_event_loop()




class Service:
    loop: asyncio.AbstractEventLoop

    def __init__(self, port: int, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.port = port
        self.loop = loop if loop else asyncio.get_event_loop()

    def process(self):
        pass