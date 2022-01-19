from typing import *
# from ..common.protocol import Request
from ..common import protocol
import asyncio
import docker
from docker import errors as docker_errors
if TYPE_CHECKING:
    from docker.models.containers import Container


class Manager:
    docker_client: docker.DockerClient
    loop: asyncio.AbstractEventLoop

    unused_ports: Set[int]
    used_ports: Set[int]

    def __init__(self, port_range: str, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.docker_client = docker.from_env()
        self.loop = loop if loop else asyncio.get_event_loop()

        start_port, end_port = port_range.split(":")
        self.unused_ports = set(port for port in range(int(start_port), int(end_port) + 1))
        self.used_ports = set()


        self.test()

    async def get_port(self) -> int:
        while True:
            if self.unused_ports:
                self.used_ports.add((port := self.unused_ports.pop()))
                return port
            await asyncio.sleep(0)

    async def free_port(self, port: int) -> None:
        if port in self.used_ports:
            self.unused_ports.add(self.unused_ports.pop())

    async def start_container(self) -> Tuple[Container, int]:
        port = await self.get_port()
        container = self.docker_client.containers.run(
            "ignition", detach=True, auto_remove=True,
        )
        return container, port

    async def process(self, process: Callable[[Tuple[str, int]], Coroutine[Any, Any, Tuple[protocol.Status, protocol.Response]]]):
        container, port = self.start_container()
        status, response = await process(("localhost", port))
        try:
            container.kill()
        except docker_errors.NotFound:
            pass
        print(status, response)

    async def test(self):
        print("starting")
        container, port = await self.start_container()
        print(container.name, container.image)
        print("ended")
        container.kill()
