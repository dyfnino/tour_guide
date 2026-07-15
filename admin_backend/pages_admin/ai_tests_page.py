"""AI 测评类型管理：名称/类型/难度，以及历史测评结果查看。"""
import streamlit as st

from db import AiTest, TestResult
from ._helpers import query_to_df, session_scope, show_table

TYPE_OPTS = ["theory", "lecture", "interview"]
DIFF_OPTS = ["beginner", "normal", "advanced"]


def render():
    st.title("🤖 AI 测评管理")
    st.caption("维护测评类型（理论/讲解/面试）；查看历史测评结果")

    tabs = st.tabs(["📋 测评类型列表", "➕ 新增类型", "✏️ 编辑/删除", "📊 历史结果"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()
    with tabs[3]:
        _render_results()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(AiTest).order_by(AiTest.id.desc()))
    show_table(df)


def _render_create():
    with st.form("ai_create"):
        name = st.text_input("名称 *")
        description = st.text_area("简介", height=80)
        c1, c2, c3 = st.columns(3)
        type_ = c1.selectbox("类型", TYPE_OPTS)
        difficulty = c2.selectbox("难度", DIFF_OPTS, index=1)
        duration = c3.number_input("预计时长(分钟)", min_value=0, value=15, step=5)
        is_active = st.checkbox("启用", value=True)

        submitted = st.form_submit_button("✅ 创建", use_container_width=True)
        if submitted:
            if not name:
                st.error("名称必填")
                return
            with session_scope() as db:
                obj = AiTest(
                    name=name, description=description, type=type_,
                    difficulty=difficulty, duration=int(duration),
                    is_active=is_active,
                )
                db.add(obj); db.commit()
                st.success(f"测评 #{obj.id} 已创建")


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(AiTest.id).order_by(AiTest.id.desc()).all()]
    if not ids:
        st.info("暂无测评类型")
        return

    aid = st.selectbox("选择测评类型", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(AiTest).filter(AiTest.id == aid).first()
        if not obj:
            return

        with st.form(f"ai_edit_{aid}"):
            name = st.text_input("名称", value=obj.name or "")
            description = st.text_area("简介", value=obj.description or "", height=80)
            c1, c2, c3 = st.columns(3)
            type_ = c1.selectbox(
                "类型", TYPE_OPTS,
                index=TYPE_OPTS.index(obj.type) if obj.type in TYPE_OPTS else 0,
            )
            difficulty = c2.selectbox(
                "难度", DIFF_OPTS,
                index=DIFF_OPTS.index(obj.difficulty) if obj.difficulty in DIFF_OPTS else 1,
            )
            duration = c3.number_input("时长(分)", min_value=0, value=int(obj.duration or 0), step=5)
            is_active = st.checkbox("启用", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除", use_container_width=True)

            if save:
                obj.name = name; obj.description = description
                obj.type = type_; obj.difficulty = difficulty
                obj.duration = int(duration); obj.is_active = is_active
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"测评 #{aid} 已删除")
                st.rerun()


def _render_results():
    st.subheader("历史测评结果")
    with session_scope() as db:
        df = query_to_df(db.query(TestResult).order_by(TestResult.id.desc()).limit(500))
    show_table(df, height=480)

    st.caption("如需删除某条结果：")
    with session_scope() as db:
        rids = [r.id for r in db.query(TestResult.id).order_by(TestResult.id.desc()).limit(500).all()]
    if rids:
        rid = st.selectbox("选择结果ID", rids, format_func=lambda i: f"#{i}")
        if st.button("🗑️ 删除该结果", key="del_result"):
            with session_scope() as db:
                obj = db.query(TestResult).filter(TestResult.id == rid).first()
                if obj:
                    db.delete(obj); db.commit()
                    st.success(f"结果 #{rid} 已删除")
                    st.rerun()