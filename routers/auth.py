import schemas
import sql
import fastapi
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

router = fastapi.APIRouter()


oath = OAuth2PasswordBearer("token/")


@router.post(
    f"/token/",
    response_model=schemas.token.TokenResponse)
async def get_token(
        data: OAuth2PasswordRequestForm = fastapi.Depends()
) -> schemas.token.TokenResponse:
    """
    endpoint that follows open API spec.

    unless you rely on the spec use the 'authenticate' endpoint instead.
    """
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            user = crud.get_by_email(data.username)
        if not user:
            raise fastapi.HTTPException(400)
        if not sql.crud.hasher.verify(user.password_hash, data.password):
            raise fastapi.HTTPException(401)
        with sql.crud.Token(session) as crud:
            crud.create(user)

        return schemas.token.TokenResponse(
            access_token=user.token.access_token, expires=user.token.expires
        )


@router.post(
    f"/authenticate/",
    response_model=schemas.user.UserResponse)
async def authenticate_user(
        data: OAuth2PasswordRequestForm = fastapi.Depends()
) -> schemas.user.UserResponse:
    """
    authenticate a user.

    can be used to log in, refresh the session and check quota details.

    only required fields are used.
    """
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            user = crud.get_by_email(data.username)
        if not user:
            raise fastapi.HTTPException(400)
        if not sql.crud.hasher.verify(user.password_hash, data.password):
            raise fastapi.HTTPException(401)
        with sql.crud.Token(session) as crud:
            crud.create(user)

        return schemas.user.UserResponse(
            id=user.id, email=user.email, token=user.token, quota=user.quota
        )


@router.post(
    f"/register/",
    status_code=201,
    response_model=schemas.user.UserResponse)
async def register_user(
        data: OAuth2PasswordRequestForm = fastapi.Depends()
) -> schemas.user.UserResponse:
    """
    registers a new user.

    only required fields are used.
    """
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            try:
                user = crud.create(data)
            except sql.errors.DuplicateEmail as e:
                raise fastapi.HTTPException(400, detail=e.details)
        with sql.crud.Token(session) as crud:
            crud.create(user)
        with sql.crud.Quota(session) as crud:
            crud.create(user)

        return schemas.user.UserResponse(
            id=user.id, email=user.email, token=user.token, quota=user.quota
        )


@router.post(
    f"/logout/",
    status_code=204)
async def logout_user(
        auth_token: str = fastapi.Depends(oath)
):
    """
    log out a user.

    destroys the session.
    """
    with sql.database.Session() as session:
        sql.crud.Token(session).delete_by_value(auth_token)
    return fastapi.Response(status_code=204)
