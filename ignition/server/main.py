from typing import *
from ..common.communicator import Communicator
from ..common import protocol
import socket
import asyncio
from pathlib import Path
import tempfile
from uuid import uuid4


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 6090))
    sock.setblocking(False)
    sock.listen()
    return sock


class Server:
    loop: asyncio.AbstractEventLoop
    communicator: Communicator
    sock: socket.socket
    languages: Dict

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop]):
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(loop)
        self.sock = setup_socket()
        self.languages = {

        }

    async def handle_connection(self, connection: socket.socket) -> None:
        request = await self.communicator.recv_request(connection)



    async def run(self) -> None:
        try:
            while True:
                connection, _ = await self.loop.sock_accept(self.sock)
                asyncio.create_task(self.handle_connection(connection))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            self.sock.close()
