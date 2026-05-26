"""后台管理简单登录：仅默认 admin / admin123，可通过环境变量覆盖。"""
import os
import streamlit as st


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def is_logged_in() -> bool:
    return bool(st.session_state.get("admin_logged_in"))


def login_form():
    st.markdown("## 🔐 后台登录")
    st.caption("仅 admin 账号可登录（默认：admin / admin123）")
    with st.form("login_form"):
        username = st.text_input("用户名", value="")
        password = st.text_input("密码", type="password", value="")
        submitted = st.form_submit_button("登录", use_container_width=True)
        if submitted:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["admin_logged_in"] = True
                st.session_state["admin_username"] = username
                st.success("登录成功，正在跳转...")
                st.rerun()
            else:
                st.error("用户名或密码错误")


def logout():
    for k in ("admin_logged_in", "admin_username"):
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


def require_login():
    if not is_logged_in():
        login_form()
        st.stop()