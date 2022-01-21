from typing import *
from ..common.communicator import Communicator
import socket
from ..common import protocol
import asyncio
import logging
from ..logger import get_logger
import docker
from collections import OrderedDict
from docker import errors as docker_errors
if TYPE_CHECKING:
    from docker.models.containers import Container


logger = get_logger(__name__, logging.INFO, stdout=True)


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 6090))
    sock.setblocking(False)
    sock.listen()
    return sock


class Server:
    communicator: Communicator
    loop: asyncio.AbstractEventLoop
    docker_client: docker.DockerClient
    sock: socket.socket
    container_clients: "OrderedDict[str, Optional[socket.socket]]"

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.container_clients = OrderedDict()

    async def get_container_client(self, container: Container) -> socket.socket:
        while True:
            if self.container_clients[container.id]:
                return self.container_clients.pop(container.id)
            await asyncio.sleep(0)

    async def start_container(self) -> Container:
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=True, extra_hosts={"host.docker.internal": "host-gateway"}
        )
        self.container_clients[container.id] = None
        return container

    async def process(self, request: protocol.Request) -> [protocol.Status, Optional[protocol.Response]]:
        container = await self.start_container()
        connection = await self.get_container_client(container)

        await self.communicator.send_request(connection, request)
        status = await self.communicator.recv_status(connection)
        logger.info(status)
        if status == protocol.Status.success:
            response = await self.communicator.recv_response(connection)
            return status, response
        return status, None

    async def run(self):
        try:
            while True:
                print("awaiting connection")
                connection, _ = await self.loop.sock_accept(self.sock)
                print("a container connected")
                for container_id, client in self.container_clients.items():
                    if not self.container_clients[container_id]:
                        self.container_clients[container_id] = connection
                        break
        except ConnectionError as e:
            print(e)

    async def test(self, request: protocol.Request):
        asyncio.create_task(self.run())
        await asyncio.sleep(0.5)
        return await self.process(request)

