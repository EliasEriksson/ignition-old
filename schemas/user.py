from pydantic import BaseModel, constr
import uuid
from sql import models
from .token import Token, TokenResponse
from .quota import Quota, QuotaResponse


class UserBase(BaseModel):
    # noinspection PyUnresolvedReferences
    email: constr(max_length=models.User.email.property.columns[0].type.length)


class UserAuthData(UserBase):
    password: constr(max_length=255)


class User(UserBase):
    id: uuid.UUID
    token: Token
    quota: Quota

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    id: uuid.UUID
    token: TokenResponse
    quota: QuotaResponse

    class Config:
        orm_mode = True
