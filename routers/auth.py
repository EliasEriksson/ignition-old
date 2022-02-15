import schemas
import sql
import fastapi

router = fastapi.APIRouter()


@router.post(f"/authenticate/", status_code=200)
async def authenticate_user(
        data: schemas.user.UserAuthData
) -> schemas.user.UserResponse:
    with sql.database.Session() as session:
        with sql.crud.User(session) as crud:
            user = crud.get_by_email(data.email)
        if not user:
            raise fastapi.HTTPException(400)
        if not sql.crud.hasher.verify(user.password_hash, data.password):
            raise fastapi.HTTPException(401)
        with sql.crud.Token(session) as crud:
            crud.update(user.token)

        return schemas.user.UserResponse(
            id=user.id, email=user.email, token=user.token, quota=user.quota
        )


@router.post(f"/register/", status_code=201)
async def register_user(
        data: schemas.user.UserAuthData
) -> schemas.user.UserResponse:
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


@router.post(f"/logout/", status_code=204)
async def logout_user(
        token: schemas.token.Token
):
    with sql.database.Session() as session:
        sql.crud.Token(session).delete_by_value(token.value)
    return fastapi.Response(status_code=204)
