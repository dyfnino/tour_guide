from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class OrderStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    COMPLETED = "completed"
    REFUNDING = "refunding"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class OrderType(str, Enum):
    PRODUCT = "product"
    COURSE = "course"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAIL = "fail"
    REJECTED = "rejected"
    CLOSED = "closed"


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
    name: str = ""
    phone: str = ""
    address: str = ""
    items: List[OrderItemCreate]


class OrderCreate(OrderBase):
    pass


class CourseOrderCreate(BaseModel):
    """课程订单：只需 course_id，无需收货信息"""
    course_id: int


class OrderUpdate(BaseModel):
    status: OrderStatus


# ===================== 退款相关 =====================

class RefundApply(BaseModel):
    """用户发起退款申请"""
    reason: str = Field(default="", max_length=255)
    # 可选：部分退款金额（元）；不传或 <=0 则按订单全额退款
    amount: Optional[float] = Field(default=None, ge=0)


class RefundReview(BaseModel):
    """后台审核：通过 / 拒绝"""
    approve: bool
    admin_remark: str = Field(default="", max_length=500)


class Refund(BaseModel):
    id: int
    order_id: int
    user_id: int
    refund_no: str
    wx_refund_id: str = ""
    amount: float
    reason: str = ""
    admin_remark: str = ""
    funds_account: str = ""
    status: RefundStatus
    applied_at: datetime
    reviewed_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===================== 订单（含退款汇总） =====================

class Order(OrderBase):
    id: int
    user_id: int
    order_no: str
    total_amount: float
    status: OrderStatus
    order_type: OrderType
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem]
    refunded_amount: float = 0.0
    refunded_at: Optional[datetime] = None
    refunds: List[Refund] = []

    class Config:
        from_attributes = True


class OrderList(BaseModel):
    id: int
    order_no: str
    total_amount: float
    status: OrderStatus
    order_type: OrderType
    created_at: datetime
    item_count: int
    name: str
    phone: str
    address: str
    items: List[OrderItem]
    refunded_amount: float = 0.0

    class Config:
        from_attributes = True