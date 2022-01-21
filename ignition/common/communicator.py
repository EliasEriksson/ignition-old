import logging
from typing import *
import socket
import asyncio
from . import protocol
import json
from ..logger import get_logger


class Communicator:
    default_int_size = 8
    default_buffer_size = 128

    loop: asyncio.AbstractEventLoop
    logger: logging.Logger

    def __init__(self, logger: logging.Logger, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.loop = loop if loop else asyncio.get_event_loop()
        self.logger = logger

    async def recv_int(self, connection: socket.socket) -> int:
        self.logger.info("waiting to receive int...")
        integer = int.from_bytes((await self.loop.sock_recv(connection, self.default_int_size)), "big", signed=False)
        self.logger.info(f"received int: {integer}")
        return integer

    async def send_int(self, connection: socket.socket, integer: int) -> None:
        self.logger.info(f"sending int: {integer}")
        await self.loop.sock_sendall(connection, integer.to_bytes(self.default_int_size, "big", signed=False))

    async def recv_status(self, connection: socket.socket) -> protocol.Status:
        self.logger.info("waiting to receive status...")
        status = protocol.Status(await self.recv_int(connection))
        self.logger.info(f"received status: {status}")
        return status

    async def send_status(self, connection: socket.socket, status: protocol.Status) -> None:
        self.logger.info(f"sending status: {status}")
        await self.send_int(connection, status.value)

    async def recv_data(self, connection: socket.socket) -> bytes:
        self.logger.info("waiting to receive data size...")
        size = await self.recv_int(connection)
        self.logger.info(f"data size is expected to be {size} bytes.")
        blob = b""
        for _ in range(int(size / self.default_buffer_size)):
            self.logger.info(f"waiting to receive {self.default_buffer_size} bytes...")
            blob += await self.loop.sock_recv(connection, self.default_buffer_size)
            self.logger.info(f"received {self.default_buffer_size} bytes.")
        self.logger.info(f"waiting to receive the last {size % self.default_buffer_size} bytes...")
        blob += await self.loop.sock_recv(connection, (size % self.default_buffer_size))
        self.logger.info(f"received the last {size % self.default_buffer_size} bytes.")
        return blob

    async def send_data(self, connection: socket.socket, payload: bytes) -> None:
        self.logger.info(f"sending payload size: {len(payload)}.")
        await self.send_int(connection, len(payload))
        self.logger.info(f"sending the payload of size {len(payload)}.")
        await self.loop.sock_sendall(connection, payload)

    async def recv_request(self, connection: socket.socket) -> protocol.Request:
        self.logger.info(f"waiting to receive a request...")
        request = json.loads(await self.recv_data(connection))
        self.logger.info(f"received request: {request}.")
        return request

    async def send_request(self, connection: socket.socket, request: protocol.Request) -> None:
        self.logger.info(f"sending request: {request}.")
        await self.send_data(connection, json.dumps(request).encode("utf-8"))

    async def recv_response(self, connection: socket.socket) -> protocol.Response:
        self.logger.info(f"waiting to receive a response...")
        response = json.loads(await self.recv_data(connection))
        self.logger.info(f"received response: {response}.")
        return response

    async def send_response(self, connection: socket.socket, response: protocol.Response) -> None:
        self.logger.info(f"sending response: {response}.")
        await self.send_data(connection, json.dumps(response).encode("utf-8"))