from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CartItemAdd(BaseModel):
    """加入购物车 / 已存在则累加数量"""
    product_id: int
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    """修改某条购物车项：数量 / 勾选状态"""
    quantity: Optional[int] = Field(default=None, gt=0)
    selected: Optional[bool] = None


class CartItemBatchSelect(BaseModel):
    """批量勾选/取消勾选"""
    selected: bool
    ids: Optional[List[int]] = None  # 不传则作用于全部


class CartItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    selected: bool
    # 冗余商品信息，便于前端直接渲染
    name: str = ""
    image: str = ""
    price: float = 0.0
    original_price: Optional[float] = None
    stock: int = 0
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """购物车汇总"""
    items: List[CartItem] = []
    total_quantity: int = 0        # 勾选项数量合计
    total_amount: float = 0.0      # 勾选项金额合计