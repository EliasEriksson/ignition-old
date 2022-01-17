from typing import *
import socket
import asyncio
import protocol
import json


class Communicator:
    default_int_size = 8
    default_buffer_size = 128

    loop: asyncio.AbstractEventLoop

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.loop = loop if loop else asyncio.get_event_loop()

    async def recv_int(self, connection: socket.socket) -> int:
        return int.from_bytes((await self.loop.sock_recv(connection, self.default_int_size)), "big", signed=False)

    async def send_int(self, connection: socket.socket, integer: int) -> None:
        await self.loop.sock_sendall(connection, integer.to_bytes(self.default_int_size, "big", signed=False))

    async def recv_status(self, connection: socket.socket) -> protocol.Status:
        return protocol.Status(self.recv_int(connection))

    async def send_status(self, connection: socket.socket, status: protocol.Status) -> None:
        await self.send_int(connection, status.value)

    async def recv_data(self, connection: socket.socket) -> bytes:
        size = await self.recv_int(connection)

        blob = b""
        for _ in range(int(size / self.default_buffer_size)):
            blob += await self.loop.sock_recv(connection, self.default_buffer_size)
        blob += await self.loop.sock_recv(connection, (size % self.default_buffer_size))
        return blob

    async def send_data(self, connection: socket.socket, payload: bytes) -> None:
        await self.send_int(connection, len(payload))
        await self.loop.sock_sendall(connection, payload)

    async def recv_request(self, connection: socket.socket) -> protocol.Request:
        return json.loads(await self.recv_data(connection))

    async def send_request(self, connection: socket.socket, request: protocol.Request) -> None:
        await self.send_data(connection, json.dumps(request).encode("utf-8"))

    async def recv_response(self, connection: socket.socket) -> protocol.Response:
        return json.loads(await self.recv_data(connection))

    async def send_response(self, connection: socket.socket, response: protocol.Response) -> None:
        await self.send_data(connection, json.dumps(response).encode("utf-8"))
