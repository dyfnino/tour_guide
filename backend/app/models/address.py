from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.session import Base


class Address(Base):
    """收货地址簿"""
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)          # 收货人姓名
    phone = Column(String(20), nullable=False)         # 联系电话
    province = Column(String(50), default="")          # 省
    city = Column(String(50), default="")              # 市
    district = Column(String(50), default="")          # 区/县
    detail = Column(String(255), nullable=False)       # 详细地址
    is_default = Column(Boolean, default=False)        # 是否默认地址
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="addresses")