from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from datetime import datetime

from ..database.session import get_db
from ..models.order import Order, OrderItem, OrderStatus, OrderType, Refund, RefundStatus
from ..models.product import Product
from ..models.course import Course
from ..models.question import UserCourse
from ..schemas.order import (
    OrderCreate, OrderUpdate, Order as OrderSchema,
    OrderList, CourseOrderCreate,
    Refund as RefundSchema, RefundApply, RefundReview,
)
from ..models.user import User
from .auth import get_current_user
from ..utils import wechatpay

router = APIRouter(prefix="/orders", tags=["orders"])


def _require_admin(user: User):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")

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
        # 重新查询并预加载 items 和 refunds
        res = await db.execute(
            select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(Order.id == db_order.id)
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
            # 重新查询并预加载 items 和 refunds，避免序列化时触发懒加载
            res = await db.execute(
                select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(Order.id == db_order.id)
            )
            return res.scalar_one()

        # 付费课程：检查是否已有未支付的订单，避免重复下单
        existing = await db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.refunds))
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
        # 重新查询并预加载 items 和 refunds，避免序列化时触发懒加载
        res = await db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.refunds))
            .where(Order.id == db_order.id)
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
        query = select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(Order.user_id == user.id)
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
            select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(Order.id == order_id, Order.user_id == user.id)
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

        # 仅允许：unpaid -> cancelled（用户取消）；paid -> completed（确认收货）
        if old_status == OrderStatus.PAID and new_status == OrderStatus.COMPLETED:
            order.status = new_status
        elif old_status == OrderStatus.UNPAID and new_status == OrderStatus.CANCELLED:
            order.status = new_status
            # 关闭微信侧订单（已下单 prepay_id 的情况）
            try:
                wechatpay.close_order(order.order_no)
            except Exception:
                pass
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
        select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(
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
        select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(
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
        select(Order).options(selectinload(Order.items), selectinload(Order.refunds)).where(Order.order_no == out_trade_no)
    )
    order = res.scalar_one_or_none()
    if not order:
        return _notify_fail("订单不存在")

    await _mark_order_paid(db, order, transaction_id=transaction_id)
    return {"code": "SUCCESS", "message": "OK"}


def _notify_fail(msg: str):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"code": "FAIL", "message": msg})


# ===================== 退款流程 =====================

REFUND_TERMINAL_STATUSES = {RefundStatus.SUCCESS, RefundStatus.FAIL,
                             RefundStatus.REJECTED, RefundStatus.CLOSED}


def _to_fen(amount_yuan: float) -> int:
    return max(1, int(round(float(amount_yuan) * 100)))


async def _refundable_amount(db: AsyncSession, order: Order) -> float:
    """订单可退款金额 = 订单金额 - 已成功退款金额 - 进行中退款金额。"""
    pending_sum = 0.0
    for r in order.refunds or []:
        if r.status in (RefundStatus.PENDING, RefundStatus.PROCESSING):
            pending_sum += float(r.amount or 0)
    return max(0.0, float(order.total_amount) - float(order.refunded_amount or 0) - pending_sum)


async def _load_order_with_refunds(db: AsyncSession, order_id: int,
                                    user_id: Optional[int] = None) -> Optional[Order]:
    q = select(Order).options(
        selectinload(Order.items),
        selectinload(Order.refunds),
    ).where(Order.id == order_id)
    if user_id is not None:
        q = q.where(Order.user_id == user_id)
    res = await db.execute(q)
    return res.scalar_one_or_none()


async def _apply_refund_success(db: AsyncSession, refund: Refund,
                                  wx_refund_id: str = "",
                                  funds_account: str = ""):
    """退款成功后的副作用：更新退款单 + 订单退款汇总 + 课程订单解除报名（全额退款时）。"""
    if refund.status == RefundStatus.SUCCESS:
        return  # 幂等
    refund.status = RefundStatus.SUCCESS
    refund.succeeded_at = datetime.utcnow()
    if wx_refund_id:
        refund.wx_refund_id = wx_refund_id
    if funds_account:
        refund.funds_account = funds_account

    res = await db.execute(
        select(Order).options(selectinload(Order.items), selectinload(Order.refunds))
        .where(Order.id == refund.order_id)
    )
    order = res.scalar_one_or_none()
    if order:
        order.refunded_amount = float(order.refunded_amount or 0) + float(refund.amount)
        order.refunded_at = datetime.utcnow()
        # 已全额退款 → 订单状态 REFUNDED；否则保留为 REFUNDING（部分退款进行中）或 PAID
        if order.refunded_amount + 1e-6 >= float(order.total_amount):
            order.status = OrderStatus.REFUNDED
            # 课程订单：全额退款解除报名
            if order.order_type == OrderType.COURSE:
                for item in order.items:
                    r2 = await db.execute(
                        select(UserCourse).where(
                            UserCourse.user_id == order.user_id,
                            UserCourse.course_id == item.product_id,
                        )
                    )
                    uc = r2.scalar_one_or_none()
                    if uc:
                        await db.delete(uc)
        else:
            # 仍有未退款金额 → 保留为已支付，便于后续继续使用
            if order.status == OrderStatus.REFUNDING:
                order.status = OrderStatus.PAID
    await db.commit()


@router.post("/{order_id}/refund", response_model=RefundSchema)
async def apply_refund(
    order_id: int,
    payload: RefundApply,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """用户发起退款申请。
    - 必须是已支付且未完成退款的订单
    - 不传 amount 默认全额退款
    - 默认进入 PENDING 等后台审核；如希望立即提交微信，请使用 admin 接口
    """
    order = await _load_order_with_refunds(db, order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in (OrderStatus.PAID, OrderStatus.COMPLETED, OrderStatus.REFUNDING):
        raise HTTPException(status_code=400, detail="订单当前状态不可退款")
    if not order.transaction_id:
        raise HTTPException(status_code=400, detail="订单缺少支付交易号，无法退款")

    refundable = await _refundable_amount(db, order)
    if refundable <= 0:
        raise HTTPException(status_code=400, detail="该订单已无可退款金额")

    amount = payload.amount if (payload.amount and payload.amount > 0) else refundable
    if amount - refundable > 1e-6:
        raise HTTPException(status_code=400, detail=f"退款金额超出可退限额 {refundable:.2f}")

    refund_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:10]}"
    refund = Refund(
        order_id=order.id,
        user_id=user.id,
        refund_no=refund_no,
        amount=float(amount),
        reason=payload.reason or "",
        status=RefundStatus.PENDING,
    )
    db.add(refund)
    # 订单标记为退款中（部分退款也置为 REFUNDING，等到款项落定再回到 PAID/REFUNDED）
    if order.status == OrderStatus.PAID or order.status == OrderStatus.COMPLETED:
        order.status = OrderStatus.REFUNDING
    await db.commit()
    await db.refresh(refund)
    return refund


@router.get("/{order_id}/refunds", response_model=List[RefundSchema])
async def list_order_refunds(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查询订单的退款记录（用户自己的订单）。"""
    order = await _load_order_with_refunds(db, order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return sorted(order.refunds or [], key=lambda r: r.id, reverse=True)


@router.get("/refunds/all", response_model=List[RefundSchema])
async def list_all_refunds(
    refund_status: Optional[RefundStatus] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """管理员：列出所有退款单（可按状态筛选）。"""
    _require_admin(user)
    q = select(Refund)
    if refund_status:
        q = q.where(Refund.status == refund_status)
    q = q.order_by(Refund.id.desc())
    res = await db.execute(q)
    return res.scalars().all()


@router.post("/refunds/{refund_id}/review", response_model=RefundSchema)
async def review_refund(
    refund_id: int,
    payload: RefundReview,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """管理员审核退款：通过则提交微信发起退款；拒绝则关闭退款单。"""
    _require_admin(user)
    res = await db.execute(select(Refund).where(Refund.id == refund_id))
    refund = res.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="退款单不存在")
    if refund.status != RefundStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态不可审核: {refund.status}")

    refund.reviewed_at = datetime.utcnow()
    refund.admin_remark = payload.admin_remark or ""

    if not payload.approve:
        # 拒绝
        refund.status = RefundStatus.REJECTED
        # 订单回退：如果当前没有��他进行中退款，订单状态回到 PAID
        order = await _load_order_with_refunds(db, refund.order_id)
        if order and order.status == OrderStatus.REFUNDING:
            still_pending = any(
                r.id != refund.id and r.status in (RefundStatus.PENDING, RefundStatus.PROCESSING)
                for r in (order.refunds or [])
            )
            if not still_pending:
                order.status = OrderStatus.PAID
        await db.commit()
        await db.refresh(refund)
        return refund

    # 审核通过 → 调用微信退款
    order = await _load_order_with_refunds(db, refund.order_id)
    if not order or not order.transaction_id:
        raise HTTPException(status_code=400, detail="订单缺少支付交易号")

    refund.status = RefundStatus.PROCESSING
    await db.commit()

    try:
        result = wechatpay.refund(
            out_refund_no=refund.refund_no,
            out_trade_no=order.order_no,
            refund_fen=_to_fen(refund.amount),
            total_fen=_to_fen(order.total_amount),
            reason=refund.reason or "用户申请退款",
        )
    except Exception as e:
        refund.status = RefundStatus.FAIL
        refund.admin_remark = (refund.admin_remark or "") + f"\n[wx error] {e}"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"微信退款失败: {e}")

    wx_refund_id = result.get("refund_id", "") if isinstance(result, dict) else ""
    funds_account = result.get("funds_account", "") if isinstance(result, dict) else ""
    wx_status = (result.get("status") or "").upper() if isinstance(result, dict) else ""

    # Mock 模式：直接同步成功；真实模式：等待异步回调
    if wechatpay.is_mock() or wx_status == "SUCCESS":
        refund.wx_refund_id = wx_refund_id
        refund.funds_account = funds_account
        await _apply_refund_success(db, refund, wx_refund_id=wx_refund_id,
                                     funds_account=funds_account)
    else:
        # 例如 PROCESSING / ABNORMAL
        if wx_refund_id:
            refund.wx_refund_id = wx_refund_id
        await db.commit()

    await db.refresh(refund)
    return refund


@router.post("/refunds/{refund_id}/query", response_model=RefundSchema)
async def query_refund_status(
    refund_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """管理员主动查询退款状态（用于回调延迟时手动同步）。"""
    _require_admin(user)
    res = await db.execute(select(Refund).where(Refund.id == refund_id))
    refund = res.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="退款单不存在")
    if refund.status in REFUND_TERMINAL_STATUSES and refund.status != RefundStatus.FAIL:
        return refund

    data = wechatpay.query_refund(refund.refund_no)
    if not data:
        return refund

    wx_status = (data.get("status") or "").upper()
    if wx_status == "SUCCESS":
        await _apply_refund_success(
            db, refund,
            wx_refund_id=data.get("refund_id", ""),
            funds_account=data.get("funds_account", ""),
        )
    elif wx_status in ("ABNORMAL",):
        refund.status = RefundStatus.FAIL
        await db.commit()
    elif wx_status == "CLOSED":
        refund.status = RefundStatus.CLOSED
        await db.commit()
    await db.refresh(refund)
    return refund


@router.post("/wechat/refund-notify")
async def wechat_refund_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    微信退款结果通知（v3）。
    必须返回 {"code":"SUCCESS","message":"OK"} 才会被视为成功。
    """
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    try:
        resource = wechatpay.parse_refund_notify(headers, body)
    except Exception as e:
        return _notify_fail(f"解析失败: {e}")
    if not resource:
        return _notify_fail("验签或解密失败")

    out_refund_no = resource.get("out_refund_no")
    if not out_refund_no:
        return _notify_fail("缺少 out_refund_no")

    res = await db.execute(select(Refund).where(Refund.refund_no == out_refund_no))
    refund = res.scalar_one_or_none()
    if not refund:
        return _notify_fail("退款单不存在")

    event_type = resource.get("__event_type", "")
    refund_status = (resource.get("refund_status") or "").upper()
    wx_refund_id = resource.get("refund_id", "")
    funds_account = resource.get("user_received_account", "") or resource.get("funds_account", "")

    if event_type == "REFUND.SUCCESS" or refund_status == "SUCCESS":
        await _apply_refund_success(db, refund, wx_refund_id=wx_refund_id,
                                     funds_account=funds_account)
    elif event_type == "REFUND.ABNORMAL" or refund_status == "ABNORMAL":
        refund.status = RefundStatus.FAIL
        await db.commit()
    elif event_type == "REFUND.CLOSED" or refund_status == "CLOSED":
        refund.status = RefundStatus.CLOSED
        await db.commit()

    return {"code": "SUCCESS", "message": "OK"}


@router.post("/{order_id}/mock-refunded")
async def mock_refunded(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mock 模式专用：把订单的所有 PENDING/PROCESSING 退款单一键置为成功。"""
    if not wechatpay.is_mock():
        raise HTTPException(status_code=403, detail="非 Mock 模式禁止调用")
    order = await _load_order_with_refunds(db, order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    changed = 0
    for refund in order.refunds or []:
        if refund.status in (RefundStatus.PENDING, RefundStatus.PROCESSING):
            await _apply_refund_success(
                db, refund,
                wx_refund_id=f"mockrefund_{uuid.uuid4().hex[:16]}",
                funds_account="支付用户零钱",
            )
            changed += 1
    return {"ok": True, "refunds_marked_success": changed}