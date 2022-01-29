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


logger = get_logger(__name__, logging.INFO, stdout=True)


def setup_socket() -> socket.socket:
    """
    helper function for setting up the tcp socket.
    """
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class Client:
    """
    ignition execution client.

    the server will open a docker container with one of these clients.
    this client will attempt to connect to the server and get a request.

    the request is then process and a response is sent back.

    after the client dies so should the process and docker container.
    """
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
        """
        processing of requests.

        receives a reqeust from the server to process.
        the requests' language is checked against the supported languages.
        if its supported the source is written to a file and passed down to the Language process method.

        a failed request will only send a status back to the server.
        a successful request will send a status followed by a response.
        """
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
        """
        connects to the server and starts the handling.

        attempts to connect to the server. if any error occurs the error is logged.
        the errors if they occur should mostly be about connection errors.

        passes the connection to the handle function
        """
        logger.info("client running...")
        try:
            connection = setup_socket()
            # domain name set by docker. will error if run outside of docker.
            await self.loop.sock_connect(connection, ("host.docker.internal", 6090))
            await self.handle_connection(connection)
        except Exception as e:
            logger.critical(e)
        finally:
            self.sock.close()
