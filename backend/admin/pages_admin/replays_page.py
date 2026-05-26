"""回放管理：URL、时长、观看数。"""
import streamlit as st

from db import Replay
from ._helpers import query_to_df, session_scope, show_table


def render():
    st.title("🎬 回放管理")
    st.caption("维护回放视频地址、时长与观看统计")

    tabs = st.tabs(["📋 回放列表", "➕ 新增回放", "✏️ 编辑/删除"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(Replay).order_by(Replay.id.desc()))
    c1, c2 = st.columns([3, 1])
    kw = c1.text_input("搜索回放标题", value="", key="replay_search")
    only_active = c2.checkbox("仅显示启用", value=False, key="replay_active")
    if not df.empty:
        if kw:
            df = df[df["title"].astype(str).str.contains(kw, case=False, na=False)]
        if only_active:
            df = df[df["is_active"] == True]  # noqa: E712
    show_table(df)


def _render_create():
    with st.form("replay_create"):
        title = st.text_input("回放标题 *")
        description = st.text_area("简介", height=80)
        c1, c2 = st.columns(2)
        live_id = c1.number_input("关联直播ID（可空）", min_value=0, value=0, step=1)
        cover_image = c2.text_input("封面图 URL")
        replay_url = st.text_input("回放视频 URL *")
        c3, c4 = st.columns(2)
        duration = c3.number_input("时长（秒）", min_value=0, value=0, step=10)
        is_active = c4.checkbox("启用", value=True)

        submitted = st.form_submit_button("✅ 创建回放", use_container_width=True)
        if submitted:
            if not title or not replay_url:
                st.error("标题与回放 URL 必填")
                return
            with session_scope() as db:
                obj = Replay(
                    live_id=int(live_id) if live_id else None,
                    title=title, description=description,
                    cover_image=cover_image or None,
                    replay_url=replay_url,
                    duration=int(duration), is_active=is_active,
                )
                db.add(obj); db.commit()
                st.success(f"回放 #{obj.id} 已创建")


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(Replay.id).order_by(Replay.id.desc()).all()]
    if not ids:
        st.info("暂无回放")
        return

    rid = st.selectbox("选择回放", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Replay).filter(Replay.id == rid).first()
        if not obj:
            return

        with st.form(f"replay_edit_{rid}"):
            title = st.text_input("标题", value=obj.title or "")
            description = st.text_area("简介", value=obj.description or "", height=80)
            c1, c2 = st.columns(2)
            live_id = c1.number_input("关联直播ID", min_value=0, value=int(obj.live_id or 0), step=1)
            cover_image = c2.text_input("封面图 URL", value=obj.cover_image or "")
            replay_url = st.text_input("回放 URL", value=obj.replay_url or "")
            c3, c4, c5 = st.columns(3)
            duration = c3.number_input("时长（秒）", min_value=0, value=int(obj.duration or 0), step=10)
            views = c4.number_input("观看数", min_value=0, value=int(obj.views or 0), step=1)
            is_active = c5.checkbox("启用", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除", use_container_width=True)

            if save:
                obj.title = title; obj.description = description
                obj.live_id = int(live_id) if live_id else None
                obj.cover_image = cover_image or None
                obj.replay_url = replay_url or None
                obj.duration = int(duration); obj.views = int(views)
                obj.is_active = is_active
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"回放 #{rid} 已删除")
                st.rerun()