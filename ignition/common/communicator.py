from typing import *
import socket
import asyncio
from . import protocol
import json


class Communicator:
    default_int_size = 8
    default_buffer_size = 128

    loop: asyncio.AbstractEventLoop

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.loop = loop if loop else asyncio.get_event_loop()

    async def recv_int(self, connection: socket.socket) -> int:
        print("waiting to receive int...")
        integer = int.from_bytes((await self.loop.sock_recv(connection, self.default_int_size)), "big", signed=False)
        print(f"received int: {integer}")
        return integer

    async def send_int(self, connection: socket.socket, integer: int) -> None:
        print(f"sending int: {integer}")
        await self.loop.sock_sendall(connection, integer.to_bytes(self.default_int_size, "big", signed=False))

    async def recv_status(self, connection: socket.socket) -> protocol.Status:
        print("waiting to receive status...")
        status = protocol.Status(await self.recv_int(connection))
        print(f"received status: {status}")
        return status

    async def send_status(self, connection: socket.socket, status: protocol.Status) -> None:
        print(f"sending status: {status}")
        await self.send_int(connection, status.value)

    async def recv_data(self, connection: socket.socket) -> bytes:
        print("waiting to receive data...")
        size = await self.recv_int(connection)
        print(f"data size is expected to be {size} bytes.")
        blob = b""
        for _ in range(int(size / self.default_buffer_size)):
            print(f"waiting to receive {self.default_buffer_size} bytes...")
            blob += await self.loop.sock_recv(connection, self.default_buffer_size)
            print(f"received {self.default_buffer_size} bytes.")
        print(f"waiting to receive the last {size % self.default_buffer_size} bytes...")
        blob += await self.loop.sock_recv(connection, (size % self.default_buffer_size))
        print(f"received the last {size % self.default_buffer_size} bytes.")
        return blob

    async def send_data(self, connection: socket.socket, payload: bytes) -> None:
        print(f"sending payload size: {len(payload)}.")
        await self.send_int(connection, len(payload))
        print(f"sending the payload of size {len(payload)}.")
        await self.loop.sock_sendall(connection, payload)

    async def recv_request(self, connection: socket.socket) -> protocol.Request:
        print(f"waiting to receive a request...")
        request = json.loads(await self.recv_data(connection))
        print(f"received request: {request}.")
        return request

    async def send_request(self, connection: socket.socket, request: protocol.Request) -> None:
        print(f"sending request: {request}.")
        await self.send_data(connection, json.dumps(request).encode("utf-8"))

    async def recv_response(self, connection: socket.socket) -> protocol.Response:
        print(f"waiting to receive a response...")
        response = json.loads(await self.recv_data(connection))
        print(f"received response: {response}.")
        return response

    async def send_response(self, connection: socket.socket, response: protocol.Response) -> None:
        print(f"sending response: {response}.")
        await self.send_data(connection, json.dumps(response).encode("utf-8"))
