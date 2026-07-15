from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, delete

from ..database.session import get_db
from ..models.cart import CartItem
from ..models.product import Product
from ..models.user import User
from ..schemas.cart import (
    CartSummary,
    CartItem as CartItemSchema,
    CartItemAdd,
    CartItemUpdate,
    CartItemBatchSelect,
)
from .auth import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


def _to_schema(item: CartItem) -> CartItemSchema:
    """把 CartItem(含 product) 组装成带商品信息的响应"""
    p = item.product
    return CartItemSchema(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        selected=bool(item.selected),
        name=(p.name if p else ""),
        image=(p.image if p and p.image else ""),
        price=float(p.price) if p else 0.0,
        original_price=float(p.original_price) if p and p.original_price is not None else None,
        stock=(p.stock if p else 0),
        is_active=bool(p.is_active) if p else False,
        created_at=item.created_at,
    )


async def _load_cart(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id.desc())
    )
    return result.scalars().all()


def _build_summary(items) -> CartSummary:
    schemas = [_to_schema(i) for i in items]
    total_qty = sum(s.quantity for s in schemas if s.selected)
    total_amount = sum(s.price * s.quantity for s in schemas if s.selected)
    return CartSummary(
        items=schemas,
        total_quantity=total_qty,
        total_amount=round(total_amount, 2),
    )


@router.get("", response_model=CartSummary)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前用户购物车（含商品信息与勾选汇总）"""
    items = await _load_cart(db, user.id)
    return _build_summary(items)


@router.post("", response_model=CartSummary)
async def add_to_cart(
    data: CartItemAdd,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """加入购物车；已存在则累加数量"""
    result = await db.execute(select(Product).where(Product.id == data.product_id))
    product = result.scalar_one_or_none()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="商品不存在或已下架")

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.product_id == data.product_id
        )
    )
    item = result.scalar_one_or_none()
    if item:
        item.quantity += data.quantity
        item.selected = True
    else:
        item = CartItem(
            user_id=user.id,
            product_id=data.product_id,
            quantity=data.quantity,
            selected=True,
        )
        db.add(item)
    await db.commit()

    items = await _load_cart(db, user.id)
    return _build_summary(items)


@router.put("/{item_id}", response_model=CartSummary)
async def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """修改购物车项：数量 / 勾选状态"""
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="购物车项不存在")

    if data.quantity is not None:
        item.quantity = data.quantity
    if data.selected is not None:
        item.selected = data.selected
    await db.commit()

    items = await _load_cart(db, user.id)
    return _build_summary(items)


@router.post("/select", response_model=CartSummary)
async def batch_select(
    data: CartItemBatchSelect,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """批量勾选/取消勾选；不传 ids 则作用于全部"""
    stmt = update(CartItem).where(CartItem.user_id == user.id).values(selected=data.selected)
    if data.ids:
        stmt = stmt.where(CartItem.id.in_(data.ids))
    await db.execute(stmt)
    await db.commit()

    items = await _load_cart(db, user.id)
    return _build_summary(items)


@router.delete("/{item_id}", response_model=CartSummary)
async def delete_cart_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除单个购物车项"""
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="购物车项不存在")
    await db.delete(item)
    await db.commit()

    items = await _load_cart(db, user.id)
    return _build_summary(items)


@router.delete("", response_model=CartSummary)
async def clear_cart(
    only_selected: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """清空购物车；only_selected=true 时仅清除已勾选项（下单后调用）"""
    stmt = delete(CartItem).where(CartItem.user_id == user.id)
    if only_selected:
        stmt = stmt.where(CartItem.selected == True)  # noqa: E712
    await db.execute(stmt)
    await db.commit()

    items = await _load_cart(db, user.id)
    return _build_summary(items)