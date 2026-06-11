"""订单管理：查看订单与订单项、变更状态、退款审核。"""
from datetime import datetime
import sys
import uuid
from pathlib import Path

import streamlit as st

from db import Order, OrderItem, Refund, RefundStatus, OrderStatus
from ._helpers import query_to_df, session_scope, show_table

# 让我们能 import backend.app.utils.wechatpay
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from app.utils import wechatpay  # noqa: E402

STATUS_OPTS = ["unpaid", "paid", "completed", "refunding", "refunded", "cancelled"]
TYPE_OPTS = ["product", "course"]

REFUND_STATUS_LABEL = {
    "pending": "待审核",
    "processing": "微信处理中",
    "success": "已退款",
    "fail": "退款失败",
    "rejected": "已拒绝",
    "closed": "已关闭",
}


def render():
    st.title("🧾 订单管理")
    st.caption("订单查看、状态变更与退款审核")

    tabs = st.tabs(["📋 订单列表", "🔍 订单详情/操作", "💸 退款审核"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_detail()
    with tabs[2]:
        _render_refunds()


def _render_list():
    c1, c2, c3 = st.columns(3)
    status = c1.selectbox("状态", ["全部"] + STATUS_OPTS, key="o_status")
    otype = c2.selectbox("类型", ["全部"] + TYPE_OPTS, key="o_type")
    kw = c3.text_input("订单号/收件人", value="", key="o_kw")

    with session_scope() as db:
        q = db.query(Order).order_by(Order.id.desc())
        df = query_to_df(q)

    if not df.empty:
        if status != "全部":
            df = df[df["status"].astype(str).str.contains(status)]
        if otype != "全部":
            df = df[df["order_type"].astype(str).str.contains(otype)]
        if kw:
            mask = df["order_no"].astype(str).str.contains(kw, case=False, na=False)
            mask |= df["name"].astype(str).str.contains(kw, case=False, na=False)
            df = df[mask]

    show_table(df, height=440)


def _render_detail():
    with session_scope() as db:
        ids = [r.id for r in db.query(Order.id).order_by(Order.id.desc()).limit(500).all()]
    if not ids:
        st.info("暂无订单")
        return

    oid = st.selectbox("选择订单", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Order).filter(Order.id == oid).first()
        if not obj:
            return

        st.markdown(f"### 订单 #{obj.id}（{obj.order_no}）")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总金额", f"￥{obj.total_amount:.2f}")
        c2.metric("当前状态", str(obj.status).split(".")[-1])
        c3.metric("已退款", f"￥{(obj.refunded_amount or 0):.2f}")
        c4.metric("用户ID", str(obj.user_id))

        st.markdown("**收货信息：**")
        st.write(f"- 收件人：{obj.name or '-'}")
        st.write(f"- 电话：{obj.phone or '-'}")
        st.write(f"- 地址：{obj.address or '-'}")

        st.markdown("**支付信息：**")
        st.write(f"- 方式：{obj.pay_method or '-'}")
        st.write(f"- prepay_id：{obj.prepay_id or '-'}")
        st.write(f"- transaction_id：{obj.transaction_id or '-'}")
        st.write(f"- paid_at：{obj.paid_at or '-'}")
        st.write(f"- refunded_at：{obj.refunded_at or '-'}")

        st.markdown("**订单项：**")
        items_df = query_to_df(db.query(OrderItem).filter(OrderItem.order_id == obj.id))
        show_table(items_df, height=200)

        st.markdown("**退款记录：**")
        refunds_df = query_to_df(db.query(Refund).filter(Refund.order_id == obj.id).order_by(Refund.id.desc()))
        show_table(refunds_df, height=200)

        st.divider()
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 状态变更")
            old_status = str(obj.status).split(".")[-1]
            new_status = st.selectbox(
                "新状态",
                STATUS_OPTS,
                index=STATUS_OPTS.index(old_status) if old_status in STATUS_OPTS else 0,
                key=f"new_status_{oid}",
            )
            if st.button("✅ 应用状态", use_container_width=True, key=f"apply_status_{oid}"):
                obj.status = new_status
                if new_status == "paid" and not obj.paid_at:
                    obj.paid_at = datetime.utcnow()
                    if not obj.pay_method:
                        obj.pay_method = "manual"
                db.commit()
                st.success(f"订单 #{oid} 状态已变更为 {new_status}")
                st.rerun()

        with col_b:
            st.markdown("#### 直接发起退款")
            refundable = float(obj.total_amount) - float(obj.refunded_amount or 0)
            # 扣除进行中
            for r in obj.refunds or []:
                if str(r.status).split(".")[-1] in ("pending", "processing"):
                    refundable -= float(r.amount or 0)
            refundable = max(0.0, refundable)
            st.info(f"剩余可退款：￥{refundable:.2f}")
            r_amount = st.number_input(
                "退款金额（元）", min_value=0.0, max_value=refundable,
                value=refundable, step=0.01, key=f"r_amt_{oid}",
            )
            r_reason = st.text_input("退款原因", value="管理员发起退款", key=f"r_reason_{oid}")
            if st.button("💸 发起退款", use_container_width=True,
                         disabled=(refundable <= 0 or not obj.transaction_id),
                         key=f"do_refund_{oid}"):
                _admin_create_and_submit_refund(db, obj, float(r_amount), r_reason)
                st.rerun()


def _render_refunds():
    """退款审核队列 + 一键操作。"""
    with session_scope() as db:
        pending = (
            db.query(Refund)
            .filter(Refund.status == RefundStatus.PENDING)
            .order_by(Refund.id.desc())
            .all()
        )
    st.markdown(f"### 待审核退款单：{len(pending)} 条")

    if not pending:
        st.success("✅ 无待审核退款单")
    else:
        for r in pending:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                c1.markdown(
                    f"**退款单 #{r.id}** ｜ 单号 `{r.refund_no}`\n\n"
                    f"订单 #{r.order_id} ｜ 用户 #{r.user_id}\n\n"
                    f"金额：￥{r.amount:.2f} ｜ 原因：{r.reason or '（未填写）'}\n\n"
                    f"申请时间：{r.applied_at}"
                )
                remark = c2.text_area("审核备注", key=f"remark_{r.id}", height=100)
                with c3:
                    if st.button("✅ 通过并退款", key=f"approve_{r.id}",
                                 use_container_width=True):
                        with session_scope() as db:
                            obj = db.query(Refund).filter(Refund.id == r.id).first()
                            order = db.query(Order).filter(Order.id == obj.order_id).first()
                            if obj and order:
                                obj.admin_remark = remark
                                _do_wx_refund(db, order, obj)
                        st.rerun()
                    if st.button("❌ 拒绝", key=f"reject_{r.id}",
                                 use_container_width=True):
                        with session_scope() as db:
                            obj = db.query(Refund).filter(Refund.id == r.id).first()
                            if obj:
                                obj.status = RefundStatus.REJECTED
                                obj.admin_remark = remark or "管理员拒绝"
                                obj.reviewed_at = datetime.utcnow()
                                # 订单状态回退
                                order = db.query(Order).filter(Order.id == obj.order_id).first()
                                if order and str(order.status).split(".")[-1] == "refunding":
                                    still_pending = any(
                                        x.id != obj.id and str(x.status).split(".")[-1] in ("pending", "processing")
                                        for x in (order.refunds or [])
                                    )
                                    if not still_pending:
                                        order.status = OrderStatus.PAID
                                db.commit()
                        st.rerun()

    st.divider()
    st.markdown("### 全部退款单")
    with session_scope() as db:
        all_df = query_to_df(db.query(Refund).order_by(Refund.id.desc()).limit(500))
    show_table(all_df, height=400)


def _admin_create_and_submit_refund(db, order: Order, amount: float, reason: str):
    """从订单详情页一键发起退款（创建退款单 + 调微信）。"""
    if not order.transaction_id:
        st.error("订单缺少支付交易号，无法退款")
        return
    refund_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:10]}"
    refund = Refund(
        order_id=order.id,
        user_id=order.user_id,
        refund_no=refund_no,
        amount=amount,
        reason=reason or "管理员发起退款",
        admin_remark="后台直接发起",
        status=RefundStatus.PENDING,
        reviewed_at=datetime.utcnow(),
    )
    db.add(refund)
    if str(order.status).split(".")[-1] in ("paid", "completed"):
        order.status = OrderStatus.REFUNDING
    db.commit()
    db.refresh(refund)
    _do_wx_refund(db, order, refund)


def _do_wx_refund(db, order: Order, refund: Refund):
    """实际调用微信退款；Mock 模式直接置为成功。"""
    try:
        result = wechatpay.refund(
            out_refund_no=refund.refund_no,
            out_trade_no=order.order_no,
            refund_fen=max(1, int(round(float(refund.amount) * 100))),
            total_fen=max(1, int(round(float(order.total_amount) * 100))),
            reason=refund.reason or "退款",
        )
    except Exception as e:
        refund.status = RefundStatus.FAIL
        refund.admin_remark = (refund.admin_remark or "") + f"\n[wx error] {e}"
        refund.reviewed_at = datetime.utcnow()
        db.commit()
        st.error(f"微信退款失败：{e}")
        return

    refund.reviewed_at = datetime.utcnow()
    refund.wx_refund_id = result.get("refund_id", "") if isinstance(result, dict) else ""
    refund.funds_account = result.get("funds_account", "") if isinstance(result, dict) else ""
    wx_status = (result.get("status") or "").upper() if isinstance(result, dict) else ""

    if wechatpay.is_mock() or wx_status == "SUCCESS":
        refund.status = RefundStatus.SUCCESS
        refund.succeeded_at = datetime.utcnow()
        order.refunded_amount = float(order.refunded_amount or 0) + float(refund.amount)
        order.refunded_at = datetime.utcnow()
        if order.refunded_amount + 1e-6 >= float(order.total_amount):
            order.status = OrderStatus.REFUNDED
        st.success(f"退款单 #{refund.id} 已成功（Mock 即时到账）")
    else:
        refund.status = RefundStatus.PROCESSING
        st.info(f"退款单 #{refund.id} 已提交微信，等待异步回调")
    db.commit()