from typing import *
from pydantic.typing import Literal as Enum
from pydantic import BaseModel, constr
from ignition.common.languages import Languages
import datetime
import uuid
from . import models


supported_languages = Enum[tuple(Languages.languages)]


# users
class UserBase(BaseModel):
    # noinspection PyUnresolvedReferences
    email: constr(max_length=models.User.email.property.columns[0].type.length)


class UserAuth(UserBase):
    password: constr(max_length=255)


class User(UserBase):
    id: uuid.UUID
    token: "Token"
    quota: "Quota"
    snippets: List["Snippet"]

    class Config:
        orm_mode = True


# tokens
class TokenBase(BaseModel):
    value: str
    expires: datetime.datetime
    user: User


class TokenCreate(TokenBase):
    pass


class Token(TokenBase):
    id: int

    class Config:
        orm_mode = True


# quota
class QuotaBase(BaseModel):
    cap: int
    current: int
    next_refresh: datetime.datetime
    user: User


class Quota(QuotaBase):
    id: int

    class Config:
        orm_mode = True


# snippets
class SnippetBase(BaseModel):
    language: Enum[supported_languages]
    # property not detected by pycharm inspection
    # noinspection PyUnresolvedReferences
    code: constr(max_length=models.Snippet.code.property.columns[0].type.length)
    # property no detected by pycharm inspection
    # noinspection PyUnresolvedReferences
    args: constr(max_length=models.Snippet.args.property.columns[0].type.length)


class SnippetCreate(SnippetBase):
    pass


class Snippet(SnippetBase):
    id: uuid.UUID
    user: User

    class Config:
        orm_mode = True


User.update_forward_refs()
