from pydantic.typing import Literal
from ignition.common.languages import Languages
from pydantic import BaseModel
import uuid


# tokens
class TokenBase(BaseModel):
    value: str


class TokenCreate(TokenBase):
    pass


class Token(TokenBase):
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

    class Config:
        orm_mode = True


supported_languages = Literal[tuple(Languages.languages)]


# snippets
class SnippetBase(BaseModel):
    language: Literal[supported_languages]
    code: str
    args: str


class SnippetCreate(SnippetBase):
    pass


class Snippet(SnippetBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
