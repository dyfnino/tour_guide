from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    nickname: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    openid: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    avatar: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class User(UserInDB):
    avatar: Optional[str] = None
    class Config:
        from_attributes = True

class WechatLogin(BaseModel):
    code: str

class LoginResponse(BaseModel):
    access_token: str
    user: User
