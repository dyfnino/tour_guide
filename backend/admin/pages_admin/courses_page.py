"""课程管理：维护视频/音频 + 封面图片（本地上传），价格、上下架。

封面图、视频、音频均通过 streamlit 上传，落地到 backend/uploads/{kind}s/ 下，
数据库里存的是后端可访问的完整 URL（例如 http://localhost:8000/uploads/images/xxx.png）。
"""
import os
import uuid
from pathlib import Path

import streamlit as st

from db import Course
from ._helpers import query_to_df, session_scope, show_table


# backend 根目录
BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = BACKEND_DIR / "uploads"

KIND_DIRS = {"image": "images", "video": "videos", "audio": "audios"}
ALLOWED_EXT = {
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"},
    "video": {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"},
    "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".silk"},
}


def _api_base() -> str:
    """返回后端可访问的基础 URL。可通过环境变量 BACKEND_BASE_URL 覆盖。"""
    return os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")


def _save_upload(uploaded_file, kind: str) -> str:
    """保存 streamlit 上传文件到 backend/uploads/<kind>/，返回访问 URL。"""
    if not uploaded_file:
        return ""
    name = uploaded_file.name or "upload"
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXT.get(kind, set()):
        raise ValueError(f"不支持的扩展名: {ext}（{kind} 允许 {sorted(ALLOWED_EXT[kind])}）")

    sub = KIND_DIRS[kind]
    target_dir = UPLOAD_ROOT / sub
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}{ext}"
    target_path = target_dir / safe_name
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return f"{_api_base()}/uploads/{sub}/{safe_name}"


def render():
    st.title("📚 课程管理")
    st.caption("课程基本信息、封面图、视频/音频文件（本地上传）、价格与上下架")

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
    with st.form("course_create", clear_on_submit=False):
        c1, c2 = st.columns(2)
        name = c1.text_input("课程名称 *")
        category = c2.text_input("分类", value="basic")
        description = st.text_area("课程描述", height=100)

        c3, c4, c5 = st.columns(3)
        price = c3.number_input("价格", min_value=0.0, value=0.0, step=10.0)
        duration = c4.number_input("课时(分钟)", min_value=0, value=0, step=10)
        level = c5.selectbox("难度/讲师", ["", "beginner", "intermediate", "advanced"])

        media_type = st.radio("媒体类型", ["video", "audio"], horizontal=True)

        st.markdown("**封面图片**（上架后用于课程列表展示）")
        cover_file = st.file_uploader(
            "上传封面图（png/jpg/webp）",
            type=list(ext.lstrip(".") for ext in ALLOWED_EXT["image"]),
            key="cover_create",
        )

        if media_type == "video":
            st.markdown("**视频文件**")
            media_file = st.file_uploader(
                "上传视频（mp4/mov/webm 等）",
                type=list(ext.lstrip(".") for ext in ALLOWED_EXT["video"]),
                key="video_create",
            )
        else:
            st.markdown("**音频文件**")
            media_file = st.file_uploader(
                "上传音频（mp3/wav/m4a 等）",
                type=list(ext.lstrip(".") for ext in ALLOWED_EXT["audio"]),
                key="audio_create",
            )

        c8, c9 = st.columns(2)
        is_free = c8.checkbox("免费课程", value=False)
        is_active = c9.checkbox("上架", value=True)

        submitted = st.form_submit_button("✅ 创建课程", use_container_width=True)
        if submitted:
            if not name:
                st.error("课程名称必填")
                return
            if not cover_file:
                st.error("请上传封面图")
                return
            if not media_file:
                st.error(f"请上传{'视频' if media_type == 'video' else '音频'}文件")
                return
            try:
                image_url = _save_upload(cover_file, "image")
                media_url = _save_upload(media_file, media_type)
            except ValueError as e:
                st.error(str(e))
                return
            with session_scope() as db:
                obj = Course(
                    name=name, category=category, description=description,
                    price=price, duration=int(duration) if duration else None,
                    level=level or None, media_type=media_type,
                    media_url=media_url, image=image_url,
                    is_free=is_free, is_active=is_active,
                )
                db.add(obj)
                db.commit()
                st.success(f"课程 #{obj.id} 创建成功（封面 + {media_type} 已上传）")


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

        # 当前封面、媒体预览（form 外）
        prev_col1, prev_col2 = st.columns(2)
        with prev_col1:
            st.markdown("**当前封面**")
            if obj.image:
                st.image(obj.image, width=200)
            else:
                st.caption("（无封面）")
        with prev_col2:
            st.markdown(f"**当前{(obj.media_type or 'video')} URL**")
            st.code(obj.media_url or "（无）", language=None)

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

            mtype_idx = 0 if (obj.media_type or "video") == "video" else 1
            media_type = st.radio("媒体类型", ["video", "audio"], index=mtype_idx, horizontal=True)

            st.markdown("**更换封面图**（留空则保留原图）")
            cover_file = st.file_uploader(
                "上传新封面",
                type=list(ext.lstrip(".") for ext in ALLOWED_EXT["image"]),
                key=f"cover_edit_{course_id}",
            )

            st.markdown("**更换媒体文件**（留空则保留原媒体）")
            media_file = st.file_uploader(
                "上传新视频/音频",
                type=list(ext.lstrip(".") for ext in
                          ALLOWED_EXT["video"] | ALLOWED_EXT["audio"]),
                key=f"media_edit_{course_id}",
            )

            c8, c9 = st.columns(2)
            is_free = c8.checkbox("免费课程", value=bool(obj.is_free))
            is_active = c9.checkbox("上架", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除课程", use_container_width=True)

            if save:
                try:
                    if cover_file:
                        obj.image = _save_upload(cover_file, "image")
                    if media_file:
                        obj.media_url = _save_upload(media_file, media_type)
                except ValueError as e:
                    st.error(str(e))
                    return
                obj.name = name; obj.category = category; obj.description = description
                obj.price = price; obj.duration = int(duration) if duration else None
                obj.level = level or None; obj.media_type = media_type
                obj.is_free = is_free; obj.is_active = is_active
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj)
                db.commit()
                st.success(f"课程 #{course_id} 已删除")
                st.rerun()