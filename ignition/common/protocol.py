from typing import *
from enum import Enum


class Status(Enum):
    """
    used to send status messages.

    all status messages represent real HTTP status codes or
    websocket status codes
    """
    waiting = 100
    success = 200
    bad_request = 400
    timeout = 408
    internal_server_error = 500
    not_implemented = 501
    close = 1000


class Request(TypedDict):
    """
    used for type hinting dictionaries with these attributes.
    """
    language: str
    args: str
    code: str


class Response(TypedDict):
    """
    used to type hinting dictionaries with these attributes.
    """
    stdout: Optional[str]
    stderr: Optional[str]
    ns: int
