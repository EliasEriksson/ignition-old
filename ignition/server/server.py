from typing import *
from ..common.communicator import Communicator
import socket
from ..common import protocol
import asyncio
import logging
from ..logger import get_logger
import docker
import docker.models.containers
import docker.errors
from collections import OrderedDict
import uuid

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

    queue_size: int
    queue: Set[uuid.UUID]
    queue_overflow: "OrderedDict[uuid.UUID, protocol.Request]"
    results: Dict[uuid.UUID, Tuple[protocol.Status, Optional[protocol.Response]]]

    def __init__(self, queue_size: int = 10, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.container_clients = OrderedDict()

        self.queue_size = queue_size
        self.queue = set()
        self.queue_overflow = OrderedDict()
        self.results = {}

        self.loop.create_task(self._run())
        self.loop.create_task(self._queue_processor())

    async def get_response(self, uid: uuid.UUID) -> Tuple[protocol.Status, protocol.Response]:
        while True:
            if uid in self.results:
                return self.results.pop(uid)
            await asyncio.sleep(0)

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

    async def schedule_process(self, request: protocol.Request) -> Tuple[protocol.Status, Optional[protocol.Response]]:
        self.queue_overflow[(uid := uuid.uuid4())] = request
        return await self.get_response(uid)

    async def process(self, uid: uuid.UUID, request: protocol.Request) -> None:
        container = await self.start_container()
        connection = await self.get_container_client(container)

        await self.communicator.send_request(connection, request)
        status = await self.communicator.recv_status(connection)
        logger.info(status)

        if status == protocol.Status.success:
            response = await self.communicator.recv_response(connection)
            self.results[uid] = (status, response)
        else:
            self.results[uid] = (status, None)

        # cleanup
        self.queue.remove(uid)
        try:
            container.kill()
        except docker.errors.NotFound:
            # oh, it was already dead (:
            pass

    async def _queue_processor(self):
        while True:
            while len(self.queue) < self.queue_size:
                try:
                    uid, request = self.queue_overflow.popitem(last=False)
                    self.queue.add(uid)
                    asyncio.create_task(self.process(uid, request))
                except KeyError:
                    break
            await asyncio.sleep(0)

    async def _run(self):
        try:
            while True:
                connection, _ = await self.loop.sock_accept(self.sock)
                for container_id, client in self.container_clients.items():
                    if not self.container_clients[container_id]:
                        self.container_clients[container_id] = connection
                        break
        except ConnectionError as e:
            print(e)

    async def test(self, request: protocol.Request):
        asyncio.create_task(self._run())
        await asyncio.sleep(0.5)
        return await self.schedule_process(request)
