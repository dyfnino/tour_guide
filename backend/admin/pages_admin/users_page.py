"""用户管理：基本信息、停用/启用、设置 is_admin。"""
import streamlit as st

from db import User
from ._helpers import query_to_df, session_scope, show_table


def render():
    st.title("👥 用户管理")
    st.caption("查看用户、修改基本信息、启停账号、设置管理员")

    tabs = st.tabs(["📋 用户列表", "✏️ 编辑用户"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_edit()


def _render_list():
    c1, c2 = st.columns([3, 1])
    kw = c1.text_input("搜索用户名/昵称/手机号", value="", key="u_search")
    only_admin = c2.checkbox("仅管理员", value=False, key="u_admin")

    with session_scope() as db:
        df = query_to_df(db.query(User).order_by(User.id.desc()))

    if not df.empty:
        if "password" in df.columns:
            df = df.drop(columns=["password"])
        if "session_key" in df.columns:
            df = df.drop(columns=["session_key"])
        if kw:
            mask = df["username"].astype(str).str.contains(kw, case=False, na=False)
            mask |= df["nickname"].astype(str).str.contains(kw, case=False, na=False)
            mask |= df["phone"].astype(str).str.contains(kw, case=False, na=False)
            df = df[mask]
        if only_admin:
            df = df[df["is_admin"] == True]  # noqa: E712
    show_table(df, height=440)


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(User.id).order_by(User.id.desc()).limit(500).all()]
    if not ids:
        st.info("暂无用户")
        return

    uid = st.selectbox("选择用户", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(User).filter(User.id == uid).first()
        if not obj:
            return

        with st.form(f"u_edit_{uid}"):
            c1, c2 = st.columns(2)
            username = c1.text_input("用户名", value=obj.username or "", disabled=True)
            nickname = c2.text_input("昵称", value=obj.nickname or "")

            c3, c4 = st.columns(2)
            phone = c3.text_input("手机号", value=obj.phone or "")
            email = c4.text_input("邮箱", value=obj.email or "")

            avatar = st.text_input("头像 URL", value=obj.avatar or "")

            c5, c6 = st.columns(2)
            is_active = c5.checkbox("启用", value=bool(obj.is_active))
            is_admin = c6.checkbox("管理员", value=bool(obj.is_admin))

            new_password = st.text_input("重置密码（留空则不修改）", type="password", value="")

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除用户", use_container_width=True)

            if save:
                obj.nickname = nickname
                obj.phone = phone or None
                obj.email = email or None
                obj.avatar = avatar or None
                obj.is_active = is_active
                obj.is_admin = is_admin
                if new_password:
                    # 复用 FastAPI 中的密码哈希
                    try:
                        from app.utils.security import get_password_hash
                        obj.password = get_password_hash(new_password)
                    except Exception:
                        obj.password = new_password  # 兜底：明文（不推荐）
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"用户 #{uid} 已删除")
                st.rerun()