from typing import *
from ..common.communicator import Communicator
import socket
from ..common import protocol
import asyncio
import logging
from ..logger import get_logger
from uuid import uuid4
from .manager import Manager


logger = get_logger(__name__, logging.INFO, stdout=True)


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class Service:
    communicator: Communicator
    loop: asyncio.AbstractEventLoop
    manager: Manager

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.manager = Manager("6090:6090", loop)
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)

    async def process(self, request: protocol.Request) -> str:
        async def process(address: Tuple[str, int]) -> Tuple[protocol.Status, Optional[protocol.Response]]:
            connection = setup_socket()
            await self.loop.sock_connect(connection, address)
            await self.communicator.send_request(connection, request)
            status = await self.communicator.recv_status(connection)
            if status == protocol.Status.success:
                response = await self.communicator.recv_response(connection)
                logger.info(response)
                return status, response

            logger.info(status)
            return status, None
        return await self.manager.process(process)
