from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.types import DECIMAL
from sqlalchemy.sql import func
from ..database.session import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2))
    image = Column(String(255))
    category = Column(String(50))  # 分类
    stock = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_new = Column(Boolean, default=False)
    is_hot = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
