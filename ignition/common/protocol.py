from typing import *
from enum import Enum


class Status(Enum):
    waiting = 100
    success = 200
    bad_request = 400
    timeout = 408
    internal_server_error = 500
    not_implemented = 501
    close = 1000


RequestTypes = Literal["file", "text"]


class Request(TypedDict):
    language: str
    args: str
    code: str


class Response(TypedDict):
    stdout: Optional[str]
    stderr: Optional[str]
    ns: float
