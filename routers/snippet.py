import fastapi
import sql
import schemas
import datetime
import uuid


router = fastapi.APIRouter()


@router.get(f"/snippets/{{id}}/")
async def get_snippets(
        id: uuid.UUID
) -> schemas.user.UserResponse:
    with sql.database.Session() as session:
        with sql.crud.Snippet(session) as crud:
            snippet = crud.get_by_id(id)
        if not snippet:
            raise fastapi.HTTPException(404)
        return snippet


@router.post(f"/snippets/")
async def create_snippets(
        data: schemas.snippet.SnippetData,
        auth: str = fastapi.Header(None)
) -> schemas.snippet.SnippetResponse:
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


@router.put(f"/snippets/{{id}}/")
async def update_snippets(
        id: uuid.UUID,
        data: schemas.snippet.SnippetData,
        auth: str = fastapi.Header(None)
) -> schemas.snippet.SnippetResponse:
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


@router.delete(f"/snippets/{{id}}/")
async def delete_snippets(
        id: uuid.UUID,
        auth: str = fastapi.Header(None)
) -> schemas.snippet.SnippetResponse:
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
