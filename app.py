import asyncio
import logging

import ignition
from fastapi import FastAPI
from pydantic import BaseModel


loop = asyncio.get_event_loop()
server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)
app = FastAPI()
root_url = "/ignition/api"


class Request(BaseModel):
    language: str
    code: str
    args: str


@app.get(f"{root_url}/process/")
async def process(request: Request):
    status, response = await server.process(dict(request))
    return {"status": status, "response": response}