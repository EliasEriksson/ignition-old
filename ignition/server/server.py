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

# logger = get_logger(__name__, logging.INFO, stdout=True)


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
    logger: logging.Logger

    queue_size: int
    queue: Set[uuid.UUID]
    queue_overflow: "OrderedDict[uuid.UUID, protocol.Request]"
    results: Dict[uuid.UUID, Tuple[protocol.Status, Optional[protocol.Response]]]
    __container_clients: List["asyncio.Future[socket.socket]"]

    def __init__(self, queue_size: int = 10, logger: Optional[logging.Logger] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.__container_clients = []
        self.logger = logger if logger else get_logger(__name__, logging.WARNING, stdout=True)

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
            await asyncio.sleep(0.01)

    async def schedule_process(self, request: protocol.Request) -> Tuple[protocol.Status, Optional[protocol.Response]]:
        self.queue_overflow[(uid := uuid.uuid4())] = request
        return await self.get_response(uid)

    async def get_container_and_connection(self) -> Tuple[Container, socket.socket]:
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=False, extra_hosts={"host.docker.internal": "host-gateway"}
        )

        future: asyncio.Future[socket.socket] = self.loop.create_future()
        self.__container_clients.append(future)
        await future
        return container, future.result()

    async def process(self, uid: uuid.UUID, request: protocol.Request) -> None:
        container, connection = await self.get_container_and_connection()

        await self.communicator.send_request(connection, request)
        status = await self.communicator.recv_status(connection)
        self.logger.info(status)
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
            while self.queue_overflow and len(self.queue) < self.queue_size:
                uid, request = self.queue_overflow.popitem(last=False)
                self.queue.add(uid)
                asyncio.create_task(self.process(uid, request))
            await asyncio.sleep(0.01)

    async def _run(self):
        try:
            while True:
                connection, _ = await self.loop.sock_accept(self.sock)
                if self.__container_clients:
                    self.__container_clients.pop(0).set_result(connection)
                else:
                    connection.close()
        except ConnectionError as e:
            print(e)
