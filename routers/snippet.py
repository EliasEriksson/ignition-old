import fastapi
import sql
import schemas
import datetime
import uuid
from fastapi.security import OAuth2PasswordBearer
import asyncio
import logging
import ignition


loop = asyncio.get_event_loop()
server = ignition.Server(10, ignition.get_logger(__name__, logging.INFO), loop=loop)

router = fastapi.APIRouter()
oath = OAuth2PasswordBearer("token/")


@router.get(
    f"/snippets/{{id}}/",
    response_model=schemas.snippet.SnippetResponse)
async def get_snippets(
        id: uuid.UUID
) -> schemas.user.UserResponse:
    """
    get the code snippet with the specified id.
    """
    with sql.database.Session() as session:
        with sql.crud.Snippet(session) as crud:
            snippet = crud.get_by_id(id)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@router.post(
    f"/snippets/",
    response_model=schemas.snippet.SnippetResponse)
async def create_snippets(
        data: schemas.snippet.SnippetData,
        auth_token: str = fastapi.Depends(oath)
) -> schemas.snippet.SnippetResponse:
    """
    create a new code snippet.
    """
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_access_token(auth_token)
            if not token or token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.create(token.user, data)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@router.post(
    f"/snippets/process/",
    response_model=schemas.process.ProcessResponse)
async def process_snippets(
        data: schemas.process.ProcessData,
        auth_token: str = fastapi.Depends(oath)
) -> schemas.process.ProcessResponse:
    """
    processes the snippet with the specified id.
    """
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_access_token(auth_token)
            if not token or token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session) as crud:
            snippet = crud.get_by_id(data.id)

    status, response = await server.process({
        "language": snippet.language,
        "code": snippet.code,
        "args": snippet.args
    })
    return schemas.process.ProcessResponse(
        status=status.value, stdout=response["stdout"], stderr=response["stderr"], ns=response["ns"]
    )


@router.put(
    f"/snippets/{{id}}/",
    response_model=schemas.snippet.SnippetResponse)
async def update_snippets(
        id: uuid.UUID,
        data: schemas.snippet.SnippetData,
        auth_token: str = fastapi.Depends(oath)
) -> schemas.snippet.SnippetResponse:
    """
    update the code snippet with the specified id.
    """
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_access_token(auth_token)
            if not token or token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.update_by_id(id, data)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@router.delete(
    f"/snippets/{{id}}/",
    response_model=schemas.snippet.SnippetResponse)
async def delete_snippets(
        id: uuid.UUID,
        auth_token: str = fastapi.Depends(oath)
) -> schemas.snippet.SnippetResponse:
    """
    delete the code snippet with the specified id.
    """
    with sql.database.Session() as session:
        with sql.crud.Token(session) as crud:
            token = crud.get_by_access_token(auth_token)
            if not token or token.expires < datetime.datetime.now():
                raise fastapi.HTTPException(401)
            crud.update(token)
        with sql.crud.Snippet(session, token) as crud:
            snippet = crud.delete_by_id(id)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet
