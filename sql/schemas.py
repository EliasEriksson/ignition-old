from typing import *
from pydantic import BaseModel
import uuid
from sqlalchemy.dialects.postgresql import UUID

# model base data
class UserBase(BaseModel):
    email: str


class SnippetBase(BaseModel):
    language: str
    code: str
    args: str


# model creation data
class UserCreate(UserBase):
    password_hash: str


class SnippetCreate(SnippetBase):
    pass


# model return data
class Snippet(SnippetBase):
    id: int

    class Config:
        orm_mode = True


class User(UserBase):
    id: uuid.UUID

    class Config:
        orm_mode = True

