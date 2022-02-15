from pydantic import BaseModel
import datetime


class TokenBase(BaseModel):
    value: str
    expires: datetime.datetime


class TokenData(TokenBase):
    pass


class Token(TokenBase):
    id: int

    class Config:
        orm_mode = True


class TokenResponse(TokenBase):
    class Config:
        orm_mode = True
