import asyncio
import logging

import ignition
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_async_engine(
    "postgres+asyncpg://ignition"
)

loop = asyncio.get_event_loop()
server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)
app = FastAPI()
root_url = "/ignition/api"


class Request(BaseModel):
    language: str
    code: str
    args: str


@app.get(f"{root_url}/snippets/")
async def get_snippets():
    pass


@app.post(f"{root_url}/snippets/")
async def post_snippets():
    pass


@app.post(f"{root_url}/snippets/")
async def put_snippets():
    pass


@app.post(f"{root_url}/snippets/")
async def delete_snippets():
    pass


@app.post(f"{root_url}/login/")
async def get_login():
    pass


@app.post(f"{root_url}/login/")
async def post_login():
    pass


@app.post(f"{root_url}/process/")
async def process(request: Request):
    status, response = await server.process(dict(request))
    return {"status": status, "response": response}
