from typing import *
from pydantic.typing import Literal as Enum
from ignition.common.languages import Languages
from pydantic import BaseModel
import datetime
import uuid


supported_languages = Enum[tuple(Languages.languages)]


# tokens
class TokenBase(BaseModel):
    value: str
    user: "User"


class TokenCreate(TokenBase):
    pass


class Token(TokenBase):
    class Config:
        orm_mode = True


# quota
class Quota(BaseModel):
    id: int
    cap: int
    current: int
    next_refresh: datetime.datetime
    user: "User"


# snippets
class SnippetBase(BaseModel):
    language: Enum[supported_languages]
    code: str
    args: str


class SnippetCreate(SnippetBase):
    pass


class Snippet(SnippetBase):
    id: uuid.UUID
    user: "User"

    class Config:
        orm_mode = True


# users
class UserBase(BaseModel):
    email: str


class UserAuth(UserBase):
    password: str


class User(UserBase):
    id: uuid.UUID
    token: Token
    quota: Quota
    snippets: List[Snippet]

    class Config:
        orm_mode = True
