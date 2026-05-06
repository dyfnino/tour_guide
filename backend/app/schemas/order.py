from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OrderStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    COMPLETED = "completed"

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price: float
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    name: str
    phone: str
    address: str
    items: List[OrderItemCreate]

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: OrderStatus

class Order(OrderBase):
    id: int
    user_id: int
    order_no: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]
    
    class Config:
        from_attributes = True

class OrderList(BaseModel):
    id: int
    order_no: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    item_count: int
    name: str
    phone: str
    address: str
    items: List[OrderItem]
    
    class Config:
        from_attributes = True
