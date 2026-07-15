"""商品管理：价格/库存/分类/标签。"""
import streamlit as st

from db import Product
from ._helpers import query_to_df, session_scope, show_table


def render():
    st.title("🛒 商品管理")
    st.caption("维护商城商品：价格、原价、库存、热销/新品标识")

    tabs = st.tabs(["📋 商品列表", "➕ 新增商品", "✏️ 编辑/删除"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(Product).order_by(Product.id.desc()))

    c1, c2 = st.columns([3, 1])
    kw = c1.text_input("搜索商品名称", value="", key="p_search")
    only_active = c2.checkbox("仅显示上架", value=False, key="p_active")

    if not df.empty:
        if kw:
            df = df[df["name"].astype(str).str.contains(kw, case=False, na=False)]
        if only_active:
            df = df[df["is_active"] == True]  # noqa: E712
    show_table(df)


def _render_create():
    with st.form("p_create"):
        c1, c2 = st.columns(2)
        name = c1.text_input("商品名称 *")
        category = c2.text_input("分类")
        description = st.text_area("商品描述", height=100)

        c3, c4 = st.columns(2)
        price = c3.number_input("现价 *", min_value=0.0, value=0.0, step=10.0)
        original_price = c4.number_input("原价", min_value=0.0, value=0.0, step=10.0)

        c5, c6 = st.columns(2)
        stock = c5.number_input("库存", min_value=0, value=0, step=1)
        image = c6.text_input("图片 URL")

        c7, c8, c9 = st.columns(3)
        is_active = c7.checkbox("上架", value=True)
        is_new = c8.checkbox("新品", value=False)
        is_hot = c9.checkbox("热销", value=False)

        submitted = st.form_submit_button("✅ 创建商品", use_container_width=True)
        if submitted:
            if not name or price <= 0:
                st.error("商品名称必填，现价必须 > 0")
                return
            with session_scope() as db:
                obj = Product(
                    name=name, category=category, description=description,
                    price=price, original_price=original_price or None,
                    stock=int(stock), image=image or None,
                    is_active=is_active, is_new=is_new, is_hot=is_hot,
                )
                db.add(obj); db.commit()
                st.success(f"商品 #{obj.id} 已创建")


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(Product.id).order_by(Product.id.desc()).all()]
    if not ids:
        st.info("暂无商品")
        return

    pid = st.selectbox("选择商品", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Product).filter(Product.id == pid).first()
        if not obj:
            return

        with st.form(f"p_edit_{pid}"):
            c1, c2 = st.columns(2)
            name = c1.text_input("商品名称", value=obj.name or "")
            category = c2.text_input("分类", value=obj.category or "")
            description = st.text_area("描述", value=obj.description or "", height=100)

            c3, c4 = st.columns(2)
            price = c3.number_input("现价", min_value=0.0, value=float(obj.price or 0), step=10.0)
            original_price = c4.number_input("原价", min_value=0.0, value=float(obj.original_price or 0), step=10.0)

            c5, c6 = st.columns(2)
            stock = c5.number_input("库存", min_value=0, value=int(obj.stock or 0), step=1)
            image = c6.text_input("图片 URL", value=obj.image or "")

            c7, c8, c9 = st.columns(3)
            is_active = c7.checkbox("上架", value=bool(obj.is_active))
            is_new = c8.checkbox("新品", value=bool(obj.is_new))
            is_hot = c9.checkbox("热销", value=bool(obj.is_hot))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除", use_container_width=True)
            if save:
                obj.name = name; obj.category = category; obj.description = description
                obj.price = price; obj.original_price = original_price or None
                obj.stock = int(stock); obj.image = image or None
                obj.is_active = is_active; obj.is_new = is_new; obj.is_hot = is_hot
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"商品 #{pid} 已删除")
                st.rerun()