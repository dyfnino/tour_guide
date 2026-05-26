"""订单管理：查看订单与订单项、变更状态。"""
from datetime import datetime
import streamlit as st

from db import Order, OrderItem
from ._helpers import query_to_df, session_scope, show_table

STATUS_OPTS = ["unpaid", "paid", "completed"]
TYPE_OPTS = ["product", "course"]


def render():
    st.title("🧾 订单管理")
    st.caption("订单查看与状态变更（不允许直接修改订单总金额）")

    tabs = st.tabs(["📋 订单列表", "🔍 订单详情/状态变更"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_detail()


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
        c2.metric("当前状态", str(obj.status))
        c3.metric("类型", str(obj.order_type))
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

        st.markdown("**订单项：**")
        items_df = query_to_df(db.query(OrderItem).filter(OrderItem.order_id == obj.id))
        show_table(items_df, height=200)

        st.divider()
        st.markdown("#### 状态变更")
        old_status = str(obj.status).split(".")[-1]
        new_status = st.selectbox("新状态", STATUS_OPTS,
                                  index=STATUS_OPTS.index(old_status) if old_status in STATUS_OPTS else 0)
        if st.button("✅ 应用状态", use_container_width=True):
            obj.status = new_status
            if new_status == "paid" and not obj.paid_at:
                obj.paid_at = datetime.utcnow()
                if not obj.pay_method:
                    obj.pay_method = "manual"
            db.commit()
            st.success(f"订单 #{oid} 状态已变更为 {new_status}")
            st.rerun()