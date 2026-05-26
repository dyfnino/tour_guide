from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database.session import Base

class OrderStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    COMPLETED = "completed"

class OrderType(str, enum.Enum):
    PRODUCT = "product"
    COURSE = "course"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_no = Column(String(32), unique=True, index=True, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.UNPAID)
    order_type = Column(SQLEnum(OrderType), nullable=False, default=OrderType.PRODUCT)
    # 收货信息（课程订单可为空）
    name = Column(String(100), default="")
    phone = Column(String(20), default="")
    address = Column(Text, default="")
    # 支付相关
    pay_method = Column(String(20), default="")          # wechat
    prepay_id = Column(String(64), default="")           # 微信预支付id
    transaction_id = Column(String(64), default="")      # 微信支付单号
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    # 通用商品/课程 ID：商品订单指向 products.id；课程订单指向 courses.id
    # 不在数据库层加外键，避免课程订单的课程 ID 与 products 主键冲突
    product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")