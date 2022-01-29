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


def setup_socket() -> socket.socket:
    """
    helper method for setting upp the tcp socket
    """
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 6090))
    sock.setblocking(False)
    sock.listen()
    return sock


class Server:
    """
    the ignition server.

    the server communicates uses the docker sdk to spawn containers containing an ignition client.
    the client will be sent a request to process and a response will be given back.

    the public API only consists of the __init__ and process methods. everything else is internal.

    when the process method is used the process is added to the queue. if there is room
    in the queue the process will start to process otherwise it will wait in overflow
    until there is room.

    when the process is processing a container is spawned using the docker sdk and a connection is
    expected to be established within max 5 seconds. if it takes longer something is wrong.

    if the connection was established the request is sent to the client for processing and the
    response will be returned.
    """
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

    def __init__(self, queue_size: int = 10,
                 logger: Optional[logging.Logger] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communicator = Communicator(logger, self.loop)
        self.sock = setup_socket()
        self.logger = logger if logger else get_logger(__name__, logging.WARNING, stdout=True)

        self.queue_size = queue_size
        self.queue = set()
        self.overflow = OrderedDict()
        self.results = {}
        self.lingering_processes = []

        self.loop.create_task(self._run())

    async def process(self, request: protocol.Request) -> Tuple[protocol.Status, Optional[protocol.Response]]:
        """
        queues the request to be processed.

        creates a future in which the result can be set.
        adds the requests in the queue and attempts to advance the queue.
        waits for the future to be set and returns the response.
        """
        future: asyncio.Future[Tuple[protocol.Status, Optional[protocol.Response]]] = self.loop.create_future()
        self.results[(uid := uuid.uuid4())] = future
        self.overflow[uid] = request
        self._advance_queue()
        await future
        _ = self.results.pop(uid)
        return future.result()

    async def _get_connection(self) -> Tuple[socket.socket, Tuple[str, int]]:
        """
        starts a container and waits to receive a connection

        starts the container and creates a future in which the connection can be defined
        from _run() whenever a connection is established.

        if connection is established within 5 seconds the connection is returned else a asyncio.TimeoutError is raised.
        """
        self.logger.debug(f"starting a container...")
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=True, extra_hosts={"host.docker.internal": "host-gateway"}
        )
        self.logger.debug(f"container '{container.short_id}' started.")

        future: asyncio.Future[Tuple[socket.socket, Tuple[str, int]]] = self.loop.create_future()
        self.logger.debug(f"waiting for a container to connect...")
        self.lingering_processes.append(future)
        try:
            await asyncio.wait_for(future, 5)
        except asyncio.TimeoutError as e:
            self.lingering_processes.remove(future)
            raise e
        result = future.result()
        self.logger.debug(f"connection from '{result[1][0]}:{result[1][1]}' received.")
        return result

    async def _process(self, uid: uuid.UUID, request: protocol.Request) -> None:
        """
        processes a request.

        starts and waits for a client to connect.
        when a client connects the requests is sent and the response is received.
        when the response is received the future created in process() is set.
        """
        self.logger.info(f"starting to process '{uid}'.")
        self.logger.debug(f"waiting for container to connect to process '{uid}'...")
        try:
            connection, (ip, port) = await self._get_connection()
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

            connection.close()
            self.logger.info(
                f"process '{uid}' ran in container from '{ip}:{port}' "
                f"and exited with status '{status}'."
            )
        except asyncio.TimeoutError:
            status = protocol.Status.internal_server_error
            self.logger.error(f"no connection from container was made. Aborting process '{uid}'.")
            self.results[uid].set_result((status, None))
            self.logger.info(
                f"process '{uid}' did not receive a connection "
                f"and exited with status '{status}'."
            )
        finally:
            self.logger.debug(f"removing process '{uid}' from queue.")
            self.queue.remove(uid)
            self._advance_queue()

    def _advance_queue(self) -> None:
        """
        advances the queue.

        moves and starts processes from overflow to the queue if there is room.

        IMPORTANT this method NEEDS to be called whenever self.queue is mutated.
        should probably make get and set property in the future.
        """
        while self.overflow and len(self.queue) < self.queue_size:
            self.logger.debug("advancing the queue.")
            uid, request = self.overflow.popitem(last=False)
            self.queue.add(uid)
            asyncio.create_task(self._process(uid, request))
        self.logger.info(
            f"current queue: {len(self.queue)} / {self.queue_size} "
            f"with overflow: {len(self.overflow)} / ∞"
        )

    async def _run(self) -> None:
        """
        handles incoming connection from clients from docker containers.

        whenever a client connects the first process in the queue is given the connection
        by setting a future.
        """
        try:
            while True:
                connection, address = await self.loop.sock_accept(self.sock)
                if self.lingering_processes:
                    self.lingering_processes.pop(0).set_result((connection, address))
                else:
                    connection.close()
        except ConnectionError:
            self.logger.debug(f"container connected but no process was waiting for a connection.")
