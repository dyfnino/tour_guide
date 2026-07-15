"""直播管理：建场次、改流地址、状态切换。"""
from datetime import datetime, timedelta

import streamlit as st

from db import Live, Replay
from ._helpers import query_to_df, session_scope, show_table

STATUS_OPTS = ["upcoming", "live", "ended"]


def render():
    st.title("📺 直播管理")
    st.caption("场次、推流地址、状态变更（变更为 ended 自动生成回放）")

    tabs = st.tabs(["📋 直播列表", "➕ 新增直播", "✏️ 编辑/删除"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(Live).order_by(Live.id.desc()))
    c1, c2 = st.columns([3, 1])
    kw = c1.text_input("搜索直播标题", value="", key="live_search")
    status = c2.selectbox("状态", ["全部"] + STATUS_OPTS, key="live_status")
    if not df.empty:
        if kw:
            df = df[df["title"].astype(str).str.contains(kw, case=False, na=False)]
        if status != "全部":
            df = df[df["status"] == status]
    show_table(df)


def _render_create():
    with st.form("live_create"):
        title = st.text_input("直播标题 *")
        description = st.text_area("简介", height=80)
        c1, c2 = st.columns(2)
        lecturer = c1.text_input("主讲人")
        cover_image = c2.text_input("封面图 URL")
        live_url = st.text_input("直播流 URL（HLS / FLV / RTMP）")

        c3, c4 = st.columns(2)
        start_time = c3.text_input("开始时间", value=(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"))
        end_time = c4.text_input("结束时间", value=(datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))

        c5, c6 = st.columns(2)
        status = c5.selectbox("状态", STATUS_OPTS, index=0)
        is_active = c6.checkbox("启用", value=True)

        submitted = st.form_submit_button("✅ 创建直播", use_container_width=True)
        if submitted:
            if not title:
                st.error("标题必填")
                return
            with session_scope() as db:
                obj = Live(
                    title=title, description=description, lecturer=lecturer,
                    cover_image=cover_image or None, live_url=live_url or None,
                    start_time=_parse_dt(start_time), end_time=_parse_dt(end_time),
                    status=status, is_active=is_active,
                )
                db.add(obj); db.commit()
                st.success(f"直播 #{obj.id} 已创建")


def _parse_dt(s: str):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            continue
    return None


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(Live.id).order_by(Live.id.desc()).all()]
    if not ids:
        st.info("暂无直播")
        return

    lid = st.selectbox("选择直播", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Live).filter(Live.id == lid).first()
        if not obj:
            return

        with st.form(f"live_edit_{lid}"):
            title = st.text_input("标题", value=obj.title or "")
            description = st.text_area("简介", value=obj.description or "", height=80)
            c1, c2 = st.columns(2)
            lecturer = c1.text_input("主讲人", value=obj.lecturer or "")
            cover_image = c2.text_input("封面图 URL", value=obj.cover_image or "")
            live_url = st.text_input("直播流 URL", value=obj.live_url or "")

            c3, c4 = st.columns(2)
            start_time = c3.text_input("开始时间", value=str(obj.start_time or ""))
            end_time = c4.text_input("结束时间", value=str(obj.end_time or ""))

            c5, c6 = st.columns(2)
            old_status = obj.status or "upcoming"
            status = c5.selectbox(
                "状态", STATUS_OPTS,
                index=STATUS_OPTS.index(old_status) if old_status in STATUS_OPTS else 0,
            )
            is_active = c6.checkbox("启用", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除", use_container_width=True)

            if save:
                obj.title = title; obj.description = description
                obj.lecturer = lecturer; obj.cover_image = cover_image or None
                obj.live_url = live_url or None
                obj.start_time = _parse_dt(start_time) or obj.start_time
                obj.end_time = _parse_dt(end_time) or obj.end_time
                obj.status = status; obj.is_active = is_active

                # 状态从非 ended 改成 ended，且没有同名回放，则自动生成
                if old_status != "ended" and status == "ended" and obj.live_url:
                    exists = db.query(Replay).filter(Replay.live_id == obj.id).first()
                    if not exists:
                        replay = Replay(
                            live_id=obj.id,
                            title=f"{obj.title}（回放）",
                            description=obj.description,
                            cover_image=obj.cover_image,
                            replay_url=obj.live_url,
                            duration=0, views=0, is_active=True,
                        )
                        db.add(replay)
                db.commit()
                st.success("已保存（如状态变 ended 已自动生成回放）")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"直播 #{lid} 已删除")
                st.rerun()