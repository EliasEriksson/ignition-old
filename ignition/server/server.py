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
    overflow: "OrderedDict[uuid.UUID, protocol.Request]"
    results: Dict[uuid.UUID, "asyncio.Future[Tuple[protocol.Status, Optional[protocol.Response]]]"]
    lingering_processes: List["asyncio.Future[Tuple[socket.socket, Tuple[str, int]]]"]

    def __init__(self, queue_size: int = 10, logger: Optional[logging.Logger] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.lingering_processes = []
        self.logger = logger if logger else get_logger(__name__, logging.WARNING, stdout=True)

        self.queue_size = queue_size
        self.queue = set()
        self.overflow = OrderedDict()
        self.results = {}

        self.loop.create_task(self._run())

    async def schedule_process(self, request: protocol.Request) -> Tuple[protocol.Status, Optional[protocol.Response]]:
        future: asyncio.Future[Tuple[protocol.Status, Optional[protocol.Response]]] = self.loop.create_future()
        self.results[(uid := uuid.uuid4())] = future
        self.overflow[uid] = request
        self.advance_queue()
        await future
        _ = self.results.pop(uid)
        return future.result()

    async def get_connection(self) -> Tuple[socket.socket, Tuple[str, int]]:
        self.logger.debug(f"starting a container...")
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=True, extra_hosts={"host.docker.internal": "host-gateway"}
        )
        self.logger.debug(f"container '{container.short_id}' started.")

        future: asyncio.Future[Tuple[socket.socket, Tuple[str, int]]] = self.loop.create_future()
        self.logger.debug(f"waiting for a container to connect...")
        self.lingering_processes.append(future)
        await future
        result = future.result()
        self.logger.debug(f"connection from '{result[1][0]}:{result[1][1]}' received.")
        return result

    async def process(self, uid: uuid.UUID, request: protocol.Request) -> None:
        self.logger.debug(f"starting to process '{uid}'.")
        self.logger.debug(f"waiting for container to connect to process '{uid}'...")
        connection, (ip, port) = await self.get_connection()
        self.logger.debug(f"connection '{ip}:{port}' connected to process '{uid}'.")
        self.logger.debug(f"sending request to connection '{ip}:{port}'.")
        await self.communicator.send_request(connection, request)
        self.logger.debug(f"waiting for status from connection '{ip}:{port}'...")
        status = await self.communicator.recv_status(connection)
        self.logger.debug(f"received status '{status}' from connection '{ip}:{port}'.")

        if status == protocol.Status.success:
            self.logger.debug(f"waiting for '{ip}:{port}' to send back a response object...")
            response = await self.communicator.recv_response(connection)
            self.logger.debug(f"received response from '{ip}:{port}'.")
            self.logger.debug(f"defining the response in process '{uid}' to response from '{ip}:{port}'.")
        else:
            self.logger.debug(f"defining the response in process '{uid}' to None since '{ip}:{port}' failed.")
            response = None
        self.results[uid].set_result((status, response))

        self.logger.debug(f"removing process '{uid}' from queue.")
        self.queue.remove(uid)
        self.advance_queue()

        connection.close()

        self.logger.info(
            f"process '{uid}' ran in container from '{ip}:{port}' "
            f"and exited with status '{status}'."
        )

    def advance_queue(self) -> None:
        if self.overflow and len(self.queue) < self.queue_size:
            self.logger.debug("advancing the queue.")
            uid, request = self.overflow.popitem(last=False)
            self.queue.add(uid)
            asyncio.create_task(self.process(uid, request))
        self.logger.info(
            f"current queue: {len(self.queue)} / {self.queue_size} "
            f"with overflow: {len(self.overflow)} / ∞"
        )

    async def _run(self):
        try:
            while True:
                connection, address = await self.loop.sock_accept(self.sock)
                if self.lingering_processes:
                    self.lingering_processes.pop(0).set_result((connection, address))
                else:
                    connection.close()
        except ConnectionError:
            self.logger.debug(f"container connected but no process was waiting for a connection.")
