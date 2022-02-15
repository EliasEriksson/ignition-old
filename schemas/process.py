from typing import *
from pydantic import BaseModel
import uuid


class ProcessBase(BaseModel):
    id: uuid.UUID


class ProcessData(ProcessBase):
    pass


class ProcessResponse(BaseModel):
    status: int
    stdout: Optional[str]
    stderr: Optional[str]
    ns: int
