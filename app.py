import asyncio
import logging

import ignition
# from fastapi import FastAPI
import fastapi
from pydantic import BaseModel
import sql
from sqlalchemy.orm import Session


loop = asyncio.get_event_loop()


server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)
app = fastapi.FastAPI()
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


@app.post(f"{root_url}/authenticate/")
async def authenticate_user(model: sql.schemas.UserAuth):
    with sql.database.Session() as session:
        return sql.crud.User(session).get_by_email(model.email)


@app.post(f"{root_url}/register/", status_code=201)
async def create_user(model: sql.schemas.UserAuth) -> sql.schemas.User:
    with sql.database.Session() as session:
        return sql.crud.User(session).create(model)


@app.post(f"{root_url}/logout/", status_code=204)
async def logout_user(token: sql.schemas.Token):
    with sql.database.Session() as session:  # type: Session
        sql.crud.Token(session).delete_by_value(token.value)
    return fastapi.Response(status_code=204)


@app.post(f"{root_url}/process/")
async def process(request: Request):
    status, response = await server.process(request.dict())
    return {"status": status, "response": response}
