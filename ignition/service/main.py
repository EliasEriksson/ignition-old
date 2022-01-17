from typing import *
from ..common.communicator import Communicator
import socket
from ..common import protocol
import asyncio
from uuid import uuid4
from functools import partial


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class Service:
    communicator: Communicator
    loop: asyncio.AbstractEventLoop

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.communicator = Communicator()
        self.loop = loop if loop else asyncio.get_event_loop()

    async def run(self, request: protocol.Request):
        connection = setup_socket()
        await self.loop.sock_connect(connection, ("localhost", 6090))
        await self.communicator.send_request(connection, request)
        status = await self.communicator.recv_status(connection)
        if status == protocol.Status.success:
            response = await self.communicator.recv_response(connection)
            print(response)
        else:
            print(status)
