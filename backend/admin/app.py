"""导游服务平台 - 后台管理系统（Streamlit）

启动：
    cd backend
    streamlit run admin/app.py
"""
import streamlit as st

from auth import require_login, logout, ADMIN_USERNAME
from db import (
    safe_count,
    User, Course, Product, Live, Replay,
    AiTest, Question, Order, TestResult,
)

st.set_page_config(
    page_title="导游服务平台 · 后台管理",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎯 导游平台后台")
        st.caption(f"管理员：{st.session_state.get('admin_username') or ADMIN_USERNAME}")

        choice = st.radio(
            "导航",
            [
                "📊 控制台",
                "📚 课程管理",
                "📝 题库管理",
                "🛒 商品管理",
                "📺 直播管理",
                "🎬 回放管理",
                "🤖 AI 测评",
                "🧾 订单管理",
                "👥 用户管理",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("🚪 退出登录", use_container_width=True):
            logout()
        return choice


def page_dashboard():
    st.title("📊 控制台")
    st.caption("系统整体数据一览")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("用户数", safe_count(User))
    col2.metric("课程数", safe_count(Course))
    col3.metric("商品数", safe_count(Product))
    col4.metric("订单数", safe_count(Order))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("题库题目", safe_count(Question))
    col6.metric("直播场次", safe_count(Live))
    col7.metric("回放数量", safe_count(Replay))
    col8.metric("AI 测评结果", safe_count(TestResult))

    st.divider()

    st.subheader("快速导航")
    qa, qb, qc = st.columns(3)
    qa.info(
        "📚 课程：维护视频/音频媒体地址、课时、价格、上下架"
    )
    qb.info(
        "📝 题库：单选/多选/判断题增删改查、答案与解析"
    )
    qc.info(
        "📺 直播：建场次、改流地址、状态切换为 ended 自动建回放"
    )

    st.divider()
    st.subheader("系统提示")
    st.write(
        "- 后台仅 `admin` 账号可登录（默认密码 admin123，可通过环境变量 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 覆盖）。\n"
        "- 后台与前端共享同一数据库，所有变更对小程序立即生效。\n"
        "- 媒体地址（音频/视频）建议放在自有 CDN（OSS/COS/七牛），且配置小程序合法域名。"
    )


def main():
    require_login()
    choice = render_sidebar()

    if choice == "📊 控制台":
        page_dashboard()
    elif choice == "📚 课程管理":
        from pages_admin import courses_page
        courses_page.render()
    elif choice == "📝 题库管理":
        from pages_admin import questions_page
        questions_page.render()
    elif choice == "🛒 商品管理":
        from pages_admin import products_page
        products_page.render()
    elif choice == "📺 直播管理":
        from pages_admin import lives_page
        lives_page.render()
    elif choice == "🎬 回放管理":
        from pages_admin import replays_page
        replays_page.render()
    elif choice == "🤖 AI 测评":
        from pages_admin import ai_tests_page
        ai_tests_page.render()
    elif choice == "🧾 订单管理":
        from pages_admin import orders_page
        orders_page.render()
    elif choice == "👥 用户管理":
        from pages_admin import users_page
        users_page.render()


if __name__ == "__main__":
    main()