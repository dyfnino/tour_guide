"""课程管理：维护视频/音频媒体地址、课时、价格、上下架。"""
import streamlit as st

from db import Course
from ._helpers import query_to_df, session_scope, show_table


def render():
    st.title("📚 课程管理")
    st.caption("维护课程基本信息、媒体类型与地址、价格与上下架")

    tabs = st.tabs(["📋 课程列表", "➕ 新增课程", "✏️ 编辑/删除"])

    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(Course).order_by(Course.id.desc()))

    col1, col2 = st.columns([3, 1])
    with col1:
        kw = st.text_input("搜索课程名称", value="", key="course_search")
    with col2:
        only_active = st.checkbox("仅显示上架", value=False, key="course_only_active")

    if not df.empty:
        if kw:
            df = df[df["name"].astype(str).str.contains(kw, case=False, na=False)]
        if only_active:
            df = df[df["is_active"] == True]  # noqa: E712

    show_table(df)


def _render_create():
    with st.form("course_create"):
        c1, c2 = st.columns(2)
        name = c1.text_input("课程名称 *")
        category = c2.text_input("分类", value="")
        description = st.text_area("课程描述", height=100)

        c3, c4, c5 = st.columns(3)
        price = c3.number_input("价格", min_value=0.0, value=0.0, step=10.0)
        duration = c4.number_input("课时(分钟)", min_value=0, value=0, step=10)
        level = c5.selectbox("难度", ["", "beginner", "intermediate", "advanced"])

        c6, c7 = st.columns(2)
        media_type = c6.selectbox("媒体类型", ["video", "audio"])
        image = c7.text_input("封面图 URL", value="")

        media_url = st.text_input("媒体地址 (视频/音频 URL) *")

        c8, c9 = st.columns(2)
        is_free = c8.checkbox("免费课程", value=False)
        is_active = c9.checkbox("上架", value=True)

        submitted = st.form_submit_button("✅ 创建课程", use_container_width=True)
        if submitted:
            if not name or not media_url:
                st.error("课程名称和媒体地址必填")
                return
            with session_scope() as db:
                obj = Course(
                    name=name, category=category, description=description,
                    price=price, duration=int(duration) if duration else None,
                    level=level or None, media_type=media_type,
                    media_url=media_url, image=image or None,
                    is_free=is_free, is_active=is_active,
                )
                db.add(obj)
                db.commit()
                st.success(f"课程 #{obj.id} 创建成功")


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(Course.id).order_by(Course.id.desc()).all()]
    if not ids:
        st.info("暂无课程")
        return

    course_id = st.selectbox("选择课程", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Course).filter(Course.id == course_id).first()
        if not obj:
            st.warning("课程不存在")
            return

        with st.form(f"course_edit_{course_id}"):
            c1, c2 = st.columns(2)
            name = c1.text_input("课程名称", value=obj.name or "")
            category = c2.text_input("分类", value=obj.category or "")
            description = st.text_area("课程描述", value=obj.description or "", height=100)

            c3, c4, c5 = st.columns(3)
            price = c3.number_input("价格", min_value=0.0, value=float(obj.price or 0), step=10.0)
            duration = c4.number_input("课时(分钟)", min_value=0, value=int(obj.duration or 0), step=10)
            level_options = ["", "beginner", "intermediate", "advanced"]
            level_idx = level_options.index(obj.level) if obj.level in level_options else 0
            level = c5.selectbox("难度", level_options, index=level_idx)

            c6, c7 = st.columns(2)
            mtype_idx = 0 if (obj.media_type or "video") == "video" else 1
            media_type = c6.selectbox("媒体类型", ["video", "audio"], index=mtype_idx)
            image = c7.text_input("封面图 URL", value=obj.image or "")

            media_url = st.text_input("媒体地址", value=obj.media_url or "")

            c8, c9 = st.columns(2)
            is_free = c8.checkbox("免费课程", value=bool(obj.is_free))
            is_active = c9.checkbox("上架", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除课程", use_container_width=True)

            if save:
                obj.name = name; obj.category = category; obj.description = description
                obj.price = price; obj.duration = int(duration) if duration else None
                obj.level = level or None; obj.media_type = media_type
                obj.image = image or None; obj.media_url = media_url
                obj.is_free = is_free; obj.is_active = is_active
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj)
                db.commit()
                st.success(f"课程 #{course_id} 已删除")
                st.rerun()