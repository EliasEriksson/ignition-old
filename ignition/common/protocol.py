from typing import *
from enum import Enum
import languages


class Status(Enum):
    waiting = 100
    success = 200
    close = 1000


RequestTypes = Literal["file", "text"]


class Request(TypedDict):
    language: str  # make more strict and based on the defined languages
    code: str


class Response(TypedDict):
    pass


def foo(a: Request):
    print(a["language"])
