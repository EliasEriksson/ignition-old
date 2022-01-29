import logging
from typing import *
from ..common.communicator import Communicator
from ..common import protocol
from ..common.languages import Languages
import socket
import asyncio
from pathlib import Path
import tempfile
from uuid import uuid4
from ..logger import get_logger
import sys


logger = get_logger(__name__, logging.INFO, stdout=True)


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class Client:
    loop: asyncio.AbstractEventLoop
    communicator: Communicator
    sock: socket.socket
    connected: bool
    process_timeout = 30

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.connected = False

    async def handle_connection(self, connection: socket.socket) -> None:
        request = await self.communicator.recv_request(connection)
        if (language := request["language"]) in Languages:
            with tempfile.TemporaryDirectory() as tempdir:
                script_path = Path(tempdir).joinpath(f"{str(uuid4())}.{language}")
                with open(script_path, "w") as script:
                    script.write(request["code"])
                try:
                    response: protocol.Response = await asyncio.wait_for(
                        Languages[language](script_path, request["args"]),
                        self.process_timeout
                    )
                    await self.communicator.send_status(connection, protocol.Status.success)
                    await self.communicator.send_response(connection, response)

                except asyncio.TimeoutError:
                    await self.communicator.send_status(connection, protocol.Status.timeout)
        else:
            await self.communicator.send_status(connection, protocol.Status.not_implemented)

    async def run(self) -> None:
        logger.info("client running...")
        try:
            connection = setup_socket()
            await self.loop.sock_connect(connection, ("host.docker.internal", 6090))
            await self.handle_connection(connection)
        except Exception as e:
            logger.critical(e)
        finally:
            self.sock.close()
