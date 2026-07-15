"""后台管理简单登录：仅默认 admin / admin123，可通过环境变量覆盖。"""
import os
import streamlit as st


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def is_logged_in() -> bool:
    return bool(st.session_state.get("admin_logged_in"))


def login_form():
    # 登录页样式：隐藏侧边栏，表单居中且不铺满整页
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stAppViewContainer"] .block-container {
            max-width: 420px;
            margin: 0 auto;
            padding-top: 8vh;
        }
        [data-testid="stForm"] {
            border: 1px solid #e3e7ef;
            border-radius: 12px;
            padding: 24px 28px;
            box-shadow: 0 6px 24px rgba(31, 42, 68, 0.08);
        }
        .login-title { text-align: center; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<h2 class="login-title">🔐 后台登录</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="login-title" style="color:#8a93a6;">仅管理员账号可登录</p>',
        unsafe_allow_html=True,
    )
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