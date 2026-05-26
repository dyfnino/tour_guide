from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
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
from ..utils import wechatpay

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
            item_amount = float(product.price) * item_data.quantity
            total_amount += item_amount
            order_item = OrderItem(
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=float(product.price),
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
        # 重新查询并预加载 items
        res = await db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == db_order.id)
        )
        return res.scalar_one()

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
    try:
        # 查找课程
        result = await db.execute(select(Course).where(Course.id == payload.course_id, Course.is_active == True))
        course = result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 免费课程直接enroll，不创建订单
        if course.is_free or (course.price is not None and float(course.price) == 0):
            # 检查是否已加入：保留原有进度，不覆盖
            res = await db.execute(
                select(UserCourse).where(UserCourse.user_id == user.id, UserCourse.course_id == course.id)
            )
            already = res.scalar_one_or_none()
            if not already:
                db.add(UserCourse(user_id=user.id, course_id=course.id, progress=0))
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
            # 重新查询并预加载 items，避免序列化时触发懒加载
            res = await db.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == db_order.id)
            )
            return res.scalar_one()

        # 付费课程：检查是否已有未支付的订单，避免重复下单
        existing = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
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
        # 重新查询并预加载 items，避免序列化时触发懒加载
        res = await db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == db_order.id)
        )
        return res.scalar_one()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建课程订单失败: {e}")


@router.get("", response_model=List[OrderList])
async def get_orders(
    status: Optional[OrderStatus] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        query = select(Order).options(selectinload(Order.items)).where(Order.user_id == user.id)
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
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id, Order.user_id == user.id)
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
        new_status = order_update.status

        # 安全加固：客户端不允许直接置 paid，必须走支付接口/回调
        if old_status == OrderStatus.UNPAID and new_status == OrderStatus.PAID:
            raise HTTPException(status_code=400, detail="请通过支付接口完成支付")

        # 仅允许：unpaid -> 取消(暂未实现)；paid -> completed（确认收货）
        if old_status == OrderStatus.PAID and new_status == OrderStatus.COMPLETED:
            order.status = new_status
        elif old_status == new_status:
            pass
        else:
            raise HTTPException(status_code=400, detail=f"非法的状态变更: {old_status} -> {new_status}")

        await db.commit()
        await db.refresh(order)
        return order

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新订单失败")


# ===================== 微信支付：发起 / 回调 / 查询 =====================

async def _enroll_courses_for_order(db: AsyncSession, order: Order, user_id: int):
    """订单为课程类型时，把课程加入用户学习列表。"""
    if order.order_type != OrderType.COURSE:
        return
    for item in order.items:
        res = await db.execute(
            select(UserCourse).where(
                UserCourse.user_id == user_id,
                UserCourse.course_id == item.product_id,
            )
        )
        if not res.scalar_one_or_none():
            db.add(UserCourse(user_id=user_id, course_id=item.product_id, progress=0))


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    发起微信支付（小程序 JSAPI）。返回 wx.requestPayment 所需参数。
    Mock 模式：返回 mock=true 的占位参数，前端可调用确认接口模拟支付成功。
    """
    res = await db.execute(
        select(Order).options(selectinload(Order.items)).where(
            Order.id == order_id, Order.user_id == user.id
        )
    )
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != OrderStatus.UNPAID:
        raise HTTPException(status_code=400, detail="订单状态不可支付")
    if not user.openid:
        raise HTTPException(status_code=400, detail="缺少 openid，请重新登录")

    amount_fen = max(1, int(round(float(order.total_amount) * 100)))
    desc = f"订单 {order.order_no}"
    try:
        params = wechatpay.jsapi_pay(
            out_trade_no=order.order_no,
            amount_fen=amount_fen,
            description=desc,
            openid=user.openid,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调起支付失败: {e}")

    order.pay_method = "wechat"
    order.prepay_id = params.get("prepay_id", "")
    await db.commit()

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "amount_fen": amount_fen,
        "pay_params": {
            "timeStamp": params["timeStamp"],
            "nonceStr": params["nonceStr"],
            "package": params["package"],
            "signType": params["signType"],
            "paySign": params["paySign"],
        },
        "mock": params.get("mock", False),
    }


async def _mark_order_paid(db: AsyncSession, order: Order, transaction_id: str = ""):
    """把订单置为 paid：写入支付凭证、enroll 课程。幂等。"""
    if order.status != OrderStatus.UNPAID:
        return
    order.status = OrderStatus.PAID
    order.paid_at = datetime.utcnow()
    if transaction_id:
        order.transaction_id = transaction_id
    await _enroll_courses_for_order(db, order, order.user_id)
    await db.commit()


@router.post("/{order_id}/mock-paid")
async def mock_paid(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mock 模式专用：前端调用 wx.requestPayment 后无法真正支付，
    直接调用此接口让后端模拟一次成功回调。仅当 WX_PAY_MOCK=1 时可用。"""
    if not wechatpay.is_mock():
        raise HTTPException(status_code=403, detail="非 Mock 模式禁止调用")
    res = await db.execute(
        select(Order).options(selectinload(Order.items)).where(
            Order.id == order_id, Order.user_id == user.id
        )
    )
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    await _mark_order_paid(db, order, transaction_id=f"mock_{uuid.uuid4().hex[:16]}")
    return {"ok": True, "status": order.status}


# 微信支付回调（注意：路径直接挂到 /orders 下，便于和当前路由组共用）
@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    微信支付结果通知（v3）。
    成功必须返回 HTTP 200 且 body 为 {"code":"SUCCESS","message":"OK"}。
    任何失败需返回 4xx/5xx，且 body 为 {"code":"FAIL","message":"原因"}。
    """
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    try:
        resource = wechatpay.parse_notify(headers, body)
    except Exception as e:
        return _notify_fail(f"解析失败: {e}")

    if not resource:
        return _notify_fail("验签或解密失败")

    out_trade_no = resource.get("out_trade_no")
    transaction_id = resource.get("transaction_id", "")
    trade_state = resource.get("trade_state", "SUCCESS")
    if not out_trade_no:
        return _notify_fail("缺少 out_trade_no")
    if trade_state != "SUCCESS":
        return _notify_fail(f"未支付成功: {trade_state}")

    res = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.order_no == out_trade_no)
    )
    order = res.scalar_one_or_none()
    if not order:
        return _notify_fail("订单不存在")

    await _mark_order_paid(db, order, transaction_id=transaction_id)
    return {"code": "SUCCESS", "message": "OK"}


def _notify_fail(msg: str):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"code": "FAIL", "message": msg})