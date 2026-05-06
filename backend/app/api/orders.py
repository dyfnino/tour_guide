from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from datetime import datetime

from ..database.session import get_db
from ..models.order import Order, OrderItem, OrderStatus
from ..models.product import Product
from ..schemas.order import OrderCreate, OrderUpdate, Order as OrderSchema, OrderList
from ..models.user import User

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("", response_model=OrderSchema)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    # 模拟当前用户，实际项目中应该使用认证系统获取
    current_user_id = 1
    try:
        # 生成订单号
        order_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        
        # 计算总金额
        total_amount = 0.0
        order_items = []
        
        for item_data in order_data.items:
            # 获取商品信息
            result = await db.execute(select(Product).where(Product.id == item_data.product_id))
            product = result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {item_data.product_id} not found"
                )
            
            # 计算商品金额
            item_amount = product.price * item_data.quantity
            total_amount += item_amount
            
            # 创建订单项
            order_item = OrderItem(
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=product.price
            )
            order_items.append(order_item)
        
        # 创建订单
        db_order = Order(
            user_id=current_user_id,
            order_no=order_no,
            total_amount=total_amount,
            status=OrderStatus.UNPAID,
            name=order_data.name,
            phone=order_data.phone,
            address=order_data.address,
            items=order_items
        )
        
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        
        return db_order
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create order"
        )

@router.get("", response_model=List[OrderList])
async def get_orders(
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 模拟当前用户，实际项目中应该使用认证系统获取
        current_user_id = 1
        # 构建查询
        query = select(Order).where(Order.user_id == current_user_id)
        
        # 根据状态过滤
        if status:
            query = query.where(Order.status == status)
        
        # 按创建时间倒序排序
        query = query.order_by(Order.created_at.desc())
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        # 转换为OrderList格式
        order_list = []
        for order in orders:
            order_list.append(OrderList(
                id=order.id,
                order_no=order.order_no,
                total_amount=order.total_amount,
                status=order.status,
                created_at=order.created_at,
                item_count=len(order.items),
                name=order.name,
                phone=order.phone,
                address=order.address,
                items=order.items
            ))
        
        return order_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )

@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 模拟当前用户，实际项目中应该使用认证系统获取
        current_user_id = 1
        result = await db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == current_user_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )

@router.put("/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 模拟当前用户，实际项目中应该使用认证系统获取
        current_user_id = 1
        result = await db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == current_user_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # 更新订单状态
        order.status = order_update.status
        
        await db.commit()
        await db.refresh(order)
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order"
        )
