from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class CourseBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal(0.00)
    image: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    category: Optional[str] = None
    is_free: bool = False

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    image: Optional[str] = None
    duration: Optional[int] = None
    level: Optional[str] = None
    category: Optional[str] = None
    is_free: Optional[bool] = None

class CourseInDB(CourseBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class Course(CourseInDB):
    class Config:
        from_attributes = True
