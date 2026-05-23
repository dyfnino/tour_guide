from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from datetime import datetime

from ..database.session import get_db
from ..models.order import Order, OrderItem, OrderStatus, OrderType
from ..models.product import Product
from ..models.course import Course
from ..models.question import UserCourse
from ..schemas.order import (
    OrderCreate, OrderUpdate, Order as OrderSchema,
    OrderList, CourseOrderCreate,
)
from ..models.user import User
from .auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", response_model=OrderSchema)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建商品订单"""
    try:
        order_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        total_amount = 0.0
        order_items = []

        for item_data in order_data.items:
            result = await db.execute(select(Product).where(Product.id == item_data.product_id))
            product = result.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail=f"商品 {item_data.product_id} 不存在")
            item_amount = product.price * item_data.quantity
            total_amount += item_amount
            order_item = OrderItem(
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=product.price,
            )
            order_items.append(order_item)

        db_order = Order(
            user_id=user.id,
            order_no=order_no,
            total_amount=total_amount,
            status=OrderStatus.UNPAID,
            order_type=OrderType.PRODUCT,
            name=order_data.name,
            phone=order_data.phone,
            address=order_data.address,
            items=order_items,
        )
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        return db_order

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="创建订单失败")


@router.post("/course", response_model=OrderSchema)
async def create_course_order(
    payload: CourseOrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建课程订单：点击"立即学习"时调用，将课程加入订单"""
    # 查找课程
    result = await db.execute(select(Course).where(Course.id == payload.course_id, Course.is_active == True))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 免费课程直接enroll，不创建订单
    if course.is_free or (course.price is not None and float(course.price) == 0):
        # 检查是否已加入
        res = await db.execute(
            select(UserCourse).where(UserCourse.user_id == user.id, UserCourse.course_id == course.id)
        )
        if not res.scalar_one_or_none():
            rec = UserCourse(user_id=user.id, course_id=course.id, progress=0)
            db.add(rec)
            await db.commit()
        # 返回一个"已完成"的虚拟订单，前端可据此跳转
        order_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        db_order = Order(
            user_id=user.id,
            order_no=order_no,
            total_amount=0,
            status=OrderStatus.COMPLETED,
            order_type=OrderType.COURSE,
            name="",
            phone="",
            address="",
            items=[OrderItem(product_id=course.id, quantity=1, price=0)],
        )
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        return db_order

    # 付费课程：检查是否已有未支付的订单，避免重复下单
    existing = await db.execute(
        select(Order).where(
            Order.user_id == user.id,
            Order.order_type == OrderType.COURSE,
            Order.status == OrderStatus.UNPAID,
        )
    )
    for o in existing.scalars().all():
        # 检查该订单是否包含此课程
        for item in o.items:
            if item.product_id == course.id:
                return o  # 返回已有未支付订单

    # 创建课程订单
    order_no = f"{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
    order_item = OrderItem(product_id=course.id, quantity=1, price=float(course.price))

    db_order = Order(
        user_id=user.id,
        order_no=order_no,
        total_amount=float(course.price),
        status=OrderStatus.UNPAID,
        order_type=OrderType.COURSE,
        name="",
        phone="",
        address="",
        items=[order_item],
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order


@router.get("", response_model=List[OrderList])
async def get_orders(
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        query = select(Order).where(Order.user_id == user.id)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc())

        result = await db.execute(query)
        orders = result.scalars().all()

        order_list = []
        for order in orders:
            order_list.append(OrderList(
                id=order.id,
                order_no=order.order_no,
                total_amount=order.total_amount,
                status=order.status,
                order_type=order.order_type,
                created_at=order.created_at,
                item_count=len(order.items),
                name=order.name or "",
                phone=order.phone or "",
                address=order.address or "",
                items=order.items,
            ))
        return order_list

    except Exception as e:
        raise HTTPException(status_code=500, detail="获取订单失败")


@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == user.id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        return order

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="获取订单失败")


@router.put("/{order_id}", response_model=OrderSchema)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == user.id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        old_status = order.status
        order.status = order_update.status

        # 支付成功时：如果是课程订单，自动enroll课程
        if old_status == OrderStatus.UNPAID and order_update.status == OrderStatus.PAID:
            if order.order_type == OrderType.COURSE:
                for item in order.items:
                    # 检查是否已加入
                    res = await db.execute(
                        select(UserCourse).where(
                            UserCourse.user_id == user.id,
                            UserCourse.course_id == item.product_id,
                        )
                    )
                    if not res.scalar_one_or_none():
                        rec = UserCourse(user_id=user.id, course_id=item.product_id, progress=0)
                        db.add(rec)

        await db.commit()
        await db.refresh(order)
        return order

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新订单失败")