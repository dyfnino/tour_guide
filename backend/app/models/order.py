from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database.session import Base


class OrderStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    COMPLETED = "completed"
    # 退款流程
    REFUNDING = "refunding"   # 用户已申请退款，等待商户/微信处理
    REFUNDED = "refunded"     # 已全额退款完成
    CANCELLED = "cancelled"   # 未支付前主动取消


class OrderType(str, enum.Enum):
    PRODUCT = "product"
    COURSE = "course"


class RefundStatus(str, enum.Enum):
    """退款单状态（与微信支付 refund_status 对应）"""
    PENDING = "pending"       # 用户已申请，后台未审核
    PROCESSING = "processing" # 已提交微信，等待结果
    SUCCESS = "success"       # 退款成功
    FAIL = "fail"             # 退款失败
    REJECTED = "rejected"     # 后台拒绝退款申请
    CLOSED = "closed"         # 已关闭


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_no = Column(String(32), unique=True, index=True, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(
        SQLEnum(OrderStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=OrderStatus.UNPAID,
    )
    order_type = Column(
        SQLEnum(OrderType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=OrderType.PRODUCT,
    )
    # 收货信息（课程订单可为空）
    name = Column(String(100), default="")
    phone = Column(String(20), default="")
    address = Column(Text, default="")
    # 支付相关
    pay_method = Column(String(20), default="")          # wechat
    prepay_id = Column(String(64), default="")           # 微信预支付id
    transaction_id = Column(String(64), default="")      # 微信支付单号
    paid_at = Column(DateTime, nullable=True)
    # 退款相关汇总（明细见 refunds 表）
    refunded_amount = Column(Float, nullable=False, default=0.0)  # 已成功退款总额
    refunded_at = Column(DateTime, nullable=True)                 # 最近一次退款成功时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")


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


class Refund(Base):
    """退款单。一个订单可有多条退款记录（部分退款多次）。"""
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 业务退款单号，发往微信
    refund_no = Column(String(64), unique=True, index=True, nullable=False)
    # 微信退款单号（refund_id），回调后回填
    wx_refund_id = Column(String(64), default="", index=True)
    # 金额（元）
    amount = Column(Float, nullable=False)
    # 申请退款原因（用户填）
    reason = Column(String(255), default="")
    # 后台备注 / 拒绝原因
    admin_remark = Column(Text, default="")
    # 退款渠道返回的资金账户
    funds_account = Column(String(32), default="")
    status = Column(
        SQLEnum(RefundStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RefundStatus.PENDING,
    )
    # 时间
    applied_at = Column(DateTime, default=datetime.utcnow)        # 用户申请时间
    reviewed_at = Column(DateTime, nullable=True)                 # 后台处理时间
    succeeded_at = Column(DateTime, nullable=True)                # 微信回调成功时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="refunds")