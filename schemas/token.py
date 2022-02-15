from pydantic import BaseModel
import datetime


class TokenBase(BaseModel):
    access_token: str
    expires: datetime.datetime


class TokenData(TokenBase):
    pass


class Token(TokenBase):
    id: int

    class Config:
        orm_mode = True


class TokenResponse(TokenBase):
    token_type = "bearer"

    class Config:
        orm_mode = True
