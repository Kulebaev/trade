from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes  = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


class Carrency(BaseModel):
    name: str
    code: str
