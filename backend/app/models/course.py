from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.types import DECIMAL
from sqlalchemy.sql import func
from ..database.session import Base

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), default=0.00)
    image = Column(String(255))
    duration = Column(Integer)  # 课时
    level = Column(String(20))  # 难度级别
    category = Column(String(50))  # 分类
    is_free = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
