from typing import *
from ..common.communicator import Communicator
import socket
from ..common import protocol
import asyncio
import logging
from ..logger import get_logger
from .manager import Manager
import docker
from docker import errors as docker_errors
if TYPE_CHECKING:
    from docker.models.containers import Container


logger = get_logger(__name__, logging.INFO, stdout=True)


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


class Service:
    communicator: Communicator
    loop: asyncio.AbstractEventLoop
    docker_client: docker.DockerClient

    unused_ports: Set[int]
    used_ports: Set[int]

    def __init__(self, ports: Dict[int, int], loop: Optional[asyncio.AbstractEventLoop] = None):
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        start, end = ports.popitem()
        self.unused_ports = set(port for port in range(start, end + 1))
        self.used_ports = set()

    async def get_port(self) -> int:
        while True:
            if self.unused_ports:
                self.used_ports.add((port := self.unused_ports.pop()))
                return port
            await asyncio.sleep(0)

    def free_port(self, port: int) -> None:
        if port in self.used_ports:
            self.unused_ports.add(self.unused_ports.pop())

    async def start_container(self) -> Tuple[Container, int]:
        port = await self.get_port()
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=True, ports={f"{port}/tcp": f"6090/tcp"}
        )
        return container, port

    async def process(self, request: protocol.Request) -> [protocol.Status, Optional[protocol.Response]]:
        container, port = await self.start_container()

        connection = setup_socket()
        while True:
            try:
                print("attempting to connect...")
                await self.loop.sock_connect(connection, ("localhost", port))
                break
            except ConnectionError:
                print("failed.")
                await asyncio.sleep(0)
        await self.communicator.send_request(connection, request)
        status = await self.communicator.recv_status(connection)

        try:
            if status == protocol.Status.success:
                response = await self.communicator.recv_response(connection)
                logger.info(response)
                return status, response
            return status, None
        finally:
            self.free_port(port)
            try:
                container.kill()
            except docker_errors.NotFound:
                pass
