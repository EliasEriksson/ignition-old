import datetime
from pydantic import BaseModel


class QuotaBase(BaseModel):
    cap: int
    current: int
    next_refresh: datetime.datetime


class QuotaData(BaseModel):
    pass


class Quota(QuotaBase):
    id: int

    class Config:
        orm_mode = True


class QuotaResponse(QuotaBase):
    class Config:
        orm_mode = True
