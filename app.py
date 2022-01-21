import asyncio
import ignition
from fastapi import FastAPI
from pydantic import BaseModel


loop = asyncio.get_event_loop()
server = ignition.Server(10, loop)
app = FastAPI()
root_url = "/ignition/api"


class Request(BaseModel):
    language: str
    code: str
    args: str


@app.get(f"{root_url}/process/")
async def process(request: Request):
    status, response = await server.schedule_process(dict(request))
    return {"status": status, "response": response}
