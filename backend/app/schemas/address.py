from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AddressBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=1, max_length=20)
    province: str = Field(default="", max_length=50)
    city: str = Field(default="", max_length=50)
    district: str = Field(default="", max_length=50)
    detail: str = Field(min_length=1, max_length=255)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    district: Optional[str] = Field(default=None, max_length=50)
    detail: Optional[str] = Field(default=None, max_length=255)
    is_default: Optional[bool] = None


class Address(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True