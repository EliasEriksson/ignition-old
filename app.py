import asyncio
import logging
import uuid
import ignition
import fastapi
import sql
import datetime


# TODO
""" 
* integrate with fastapi auth.
* implement logic for rate limit.
* add proper error messages to all HTTPExceptions.
* split endpoint across multiple files for structure.
* add char limit to snippets.
* add endpoint for supported languages.
* implement password reset. (very low prio)
* implement email verification. (very low prio)
* implement mail change (very low prio)
"""

loop = asyncio.get_event_loop()

server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)
root_url = "/ignition/api"
app = fastapi.FastAPI(
    docs_url=f"{root_url}/docs",
    openapi_url=f"{root_url}/openapi.json"
)


@app.get(f"{root_url}/snippets/{{id}}/")
async def get_snippets(id: uuid.UUID):
    with sql.database.Session() as session:
        with sql.crud.Snippet(session) as crud:
            snippet = crud.get_by_id(id)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@app.post(f"{root_url}/snippets/")
async def create_snippets(
        data: sql.schemas.SnippetCreate,
        auth: str = fastapi.Header(None)
) -> sql.schemas.Snippet:
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_header(auth)
            if token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.create(token.user, data)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@app.put(f"{root_url}/snippets/{{id}}/")
async def update_snippets(
        id: uuid.UUID,
        data: sql.schemas.SnippetCreate,
        auth: str = fastapi.Header(None)
) -> sql.schemas.Snippet:
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_header(auth)
            if token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.update_by_id(id, data)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@app.delete(f"{root_url}/snippets/{{id}}/")
async def delete_snippets(
        id: uuid.UUID,
        auth: str = fastapi.Header(None)
) -> sql.schemas.Snippet:
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_header(auth)
            if token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.delete_by_id(id)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@app.post(f"{root_url}/authenticate/", status_code=200)
async def authenticate_user(
        data: sql.schemas.UserAuth
):
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            user = crud.get_by_email(data.email)
        if not user:
            return fastapi.Response(status_code=400)
        if not sql.crud.hasher.verify(user.password_hash, data.password):
            return fastapi.Response(status_code=401)

        with sql.crud.Token(session) as crud:
            crud.create(user)

        return sql.schemas.User(
            id=user.id, email=user.email, token=user.token
        )


@app.post(f"{root_url}/register/", status_code=201)
async def create_user(
        data: sql.schemas.UserAuth
) -> sql.schemas.User:
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            try:
                user = crud.create(data)
            except sql.errors.DuplicateEmail as e:
                raise fastapi.HTTPException(400, detail=e.details)
        with sql.crud.Token(session) as crud:
            crud.create(user)
        return sql.schemas.User(
            id=user.id, email=user.email, token=user.token
        )


@app.post(f"{root_url}/logout/", status_code=204)
async def logout_user(
        token: sql.schemas.Token
):
    with sql.database.Session() as session:
        sql.crud.Token(session).delete_by_value(token.value)
    return fastapi.Response(status_code=204)


@app.post(f"{root_url}/process/")
async def process(request: sql.schemas.SnippetBase):
    status, response = await server.process(request.dict())
    return {"status": status, "response": response}
