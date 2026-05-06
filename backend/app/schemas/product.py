from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    image: Optional[str] = None
    category: Optional[str] = None
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    image: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None

class ProductInDB(ProductBase):
    id: int
    sales: int
    is_active: bool
    is_new: bool
    is_hot: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class Product(ProductInDB):
    class Config:
        from_attributes = True
