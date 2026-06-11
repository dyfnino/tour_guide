"""题库管理：单选/多选/判断题增删改查、答案与解析、批量导入。"""
import json
import io
import streamlit as st

from db import Question
from ._helpers import query_to_df, session_scope, show_table

TYPE_LABELS = {"single": "单选题", "multi": "多选题", "judge": "判断题"}


def render():
    st.title("📝 题库管理")
    st.caption("维护考试刷题与模拟考试的题库")

    tabs = st.tabs(["📋 题目列表", "➕ 新增题目", "✏️ 编辑/删除", "📥 批量导入"])
    with tabs[0]:
        _render_list()
    with tabs[1]:
        _render_create()
    with tabs[2]:
        _render_edit()
    with tabs[3]:
        _render_batch_import()


def _render_list():
    with session_scope() as db:
        df = query_to_df(db.query(Question).order_by(Question.id.desc()))

    col1, col2, col3 = st.columns(3)
    kw = col1.text_input("搜索题干", value="", key="q_search")
    qtype = col2.selectbox("题型", ["全部", "single", "multi", "judge"], key="q_type")
    category = col3.text_input("分类", value="", key="q_cat")

    if not df.empty:
        if kw:
            df = df[df["title"].astype(str).str.contains(kw, case=False, na=False)]
        if qtype != "全部":
            df = df[df["type"] == qtype]
        if category:
            df = df[df["category"].astype(str).str.contains(category, case=False, na=False)]

    show_table(df, height=420)


def _format_answer(qtype: str, answer):
    """把 selectbox/multiselect 选择转成存库的 answer 值。"""
    if qtype == "multi":
        return list(answer) if isinstance(answer, (list, tuple)) else [answer]
    return int(answer) if answer is not None else 0


def _render_create():
    with st.form("q_create"):
        qtype = st.selectbox("题型 *", ["single", "multi", "judge"], format_func=lambda x: TYPE_LABELS[x])
        title = st.text_area("题干 *", height=80)
        c1, c2 = st.columns(2)
        category = c1.text_input("分类", value="basic")
        difficulty = c2.selectbox("难度", ["easy", "normal", "hard"], index=1)

        if qtype == "judge":
            options = ["正确", "错误"]
            st.text("选项：正确 / 错误（自动）")
            ans = st.radio("正确答案", [0, 1], format_func=lambda i: options[i], horizontal=True)
        else:
            opt_text = st.text_area(
                "选项（每行一个，至少2个）*",
                value="A 选项内容\nB 选项内容\nC 选项内容\nD 选项内容",
                height=120,
            )
            options = [o.strip() for o in opt_text.splitlines() if o.strip()]
            if qtype == "single":
                ans = st.radio(
                    "正确答案",
                    list(range(len(options))) if options else [0],
                    format_func=lambda i: f"{chr(65 + i)}. {options[i]}" if options else "",
                    horizontal=True,
                )
            else:
                ans = st.multiselect(
                    "正确答案（多选）",
                    list(range(len(options))) if options else [],
                    format_func=lambda i: f"{chr(65 + i)}. {options[i]}" if options else "",
                )

        analysis = st.text_area("解析", height=80)
        is_active = st.checkbox("启用", value=True)

        submitted = st.form_submit_button("✅ 创建题目", use_container_width=True)
        if submitted:
            if not title:
                st.error("题干必填")
                return
            if qtype != "judge" and len(options) < 2:
                st.error("至少 2 个选项")
                return
            if qtype == "multi" and not ans:
                st.error("多选题至少选一个正确答案")
                return
            with session_scope() as db:
                obj = Question(
                    type=qtype, title=title, options=options,
                    answer=_format_answer(qtype, ans),
                    analysis=analysis, category=category,
                    difficulty=difficulty, is_active=is_active,
                )
                db.add(obj)
                db.commit()
                st.success(f"题目 #{obj.id} 已创建")


def _render_edit():
    with session_scope() as db:
        ids = [r.id for r in db.query(Question.id).order_by(Question.id.desc()).limit(500).all()]
    if not ids:
        st.info("暂无题目")
        return

    qid = st.selectbox("选择题目", ids, format_func=lambda i: f"#{i}")
    with session_scope() as db:
        obj = db.query(Question).filter(Question.id == qid).first()
        if not obj:
            return

        with st.form(f"q_edit_{qid}"):
            qtype = st.selectbox(
                "题型", ["single", "multi", "judge"],
                index=["single", "multi", "judge"].index(obj.type),
                format_func=lambda x: TYPE_LABELS[x],
            )
            title = st.text_area("题干", value=obj.title or "", height=80)
            c1, c2 = st.columns(2)
            category = c1.text_input("分类", value=obj.category or "")
            diff_opts = ["easy", "normal", "hard"]
            difficulty = c2.selectbox(
                "难度", diff_opts,
                index=diff_opts.index(obj.difficulty) if obj.difficulty in diff_opts else 1,
            )

            current_options = obj.options or []
            current_ans = obj.answer

            if qtype == "judge":
                options = ["正确", "错误"]
                cur = int(current_ans) if isinstance(current_ans, int) else 0
                ans = st.radio("正确答案", [0, 1], index=cur,
                               format_func=lambda i: options[i], horizontal=True)
            else:
                opt_text = st.text_area(
                    "选项（每行一个）",
                    value="\n".join(current_options),
                    height=120,
                )
                options = [o.strip() for o in opt_text.splitlines() if o.strip()]
                if qtype == "single":
                    cur = int(current_ans) if isinstance(current_ans, int) else 0
                    ans = st.radio(
                        "正确答案", list(range(len(options))) if options else [0],
                        index=min(cur, max(len(options) - 1, 0)),
                        format_func=lambda i: f"{chr(65+i)}. {options[i]}" if options else "",
                        horizontal=True,
                    )
                else:
                    default = current_ans if isinstance(current_ans, list) else [current_ans] if current_ans is not None else []
                    ans = st.multiselect(
                        "正确答案（多选）",
                        list(range(len(options))) if options else [],
                       default=[i for i in default if isinstance(i, int) and i < len(options)],
                        format_func=lambda i: f"{chr(65+i)}. {options[i]}" if options else "",
                    )

            analysis = st.text_area("解析", value=obj.analysis or "", height=80)
            is_active = st.checkbox("启用", value=bool(obj.is_active))

            cs, cd = st.columns(2)
            save = cs.form_submit_button("💾 保存修改", use_container_width=True)
            delete = cd.form_submit_button("🗑️ 删除", use_container_width=True)

            if save:
                obj.type = qtype; obj.title = title; obj.options = options
                obj.answer = _format_answer(qtype, ans)
                obj.analysis = analysis; obj.category = category
                obj.difficulty = difficulty; obj.is_active = is_active
                db.commit()
                st.success("已保存")
                st.rerun()
            if delete:
                db.delete(obj); db.commit()
                st.success(f"题目 #{qid} 已删除")
                st.rerun()


def _render_batch_import():
    """批量导入题目：支持 Excel (.xlsx/.xls) 和 CSV 文件。"""
    st.subheader("📥 批量导入题目")
    st.markdown("""
**文件格式要求（Excel 或 CSV）：**

| 列名 | 必填 | 说明 |
|------|------|------|
| type | 是 | 题型：single（单选）/ multi（多选）/ judge（判断） |
| title | 是 | 题干内容 |
| options | 是 | 选项，用 `|` 分隔。如：`选项A|选项B|选项C|选项D`；判断题填 `正确|错误` |
| answer | 是 | 正确答案索引（从0开始）。单选/判断填数字如 `0`；多选用 `|` 分隔如 `0|2` |
| analysis | 否 | 解析 |
| category | 否 | 分类（如 basic / business / policy / local） |
| difficulty | 否 | 难度（easy / normal / hard），默认 normal |

    """)

    # 下载模板
    template_csv = "type,title,options,answer,analysis,category,difficulty\nsingle,中国的首都是哪个城市？,北京|上海|广州|深圳,0,北京是中华人民共和国的首都,basic,easy\nmulti,以下哪些属于世界文化遗产？,长城|故宫|天安门广场|莫高窟,0|1|3,长城、故宫和莫高窟均为世界文化遗产,local,normal\njudge,导游人员必须持证上岗,正确|错误,0,根据《导游人员管理条例》规定,policy,easy\n"
    st.download_button(
        "⬇️ 下载 CSV 模板",
        data=template_csv.encode("utf-8-sig"),
        file_name="题库导入模板.csv",
        mime="text/csv",
    )

    uploaded = st.file_uploader(
        "上传文件（支持 .xlsx / .xls / .csv）",
        type=["xlsx", "xls", "csv"],
        key="q_batch_upload",
    )

    if uploaded:
        try:
            import pandas as pd
        except ImportError:
            st.error("需要安装 pandas 和 openpyxl：pip install pandas openpyxl")
            return

        try:
            fname = uploaded.name.lower()
            if fname.endswith(".csv"):
                df = pd.read_csv(uploaded, dtype=str, keep_default_na=False)
            else:
                df = pd.read_excel(uploaded, dtype=str, keep_default_na=False)
        except Exception as e:
            st.error(f"文件解析失败：{e}")
            return

        # 检查必填列
        required_cols = {"type", "title", "options", "answer"}
        missing = required_cols - set(df.columns)
        if missing:
            st.error(f"缺少必填列：{', '.join(missing)}")
            return

        st.success(f"已读取 {len(df)} 行数据")
        st.dataframe(df.head(10), use_container_width=True)

        # 校验数据
        errors = []
        valid_types = {"single", "multi", "judge"}
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel/CSV 行号（含表头）
            if row["type"] not in valid_types:
                errors.append(f"第{row_num}行：type 必须为 single/multi/judge，实际为「{row['type']}」")
            if not row["title"].strip():
                errors.append(f"第{row_num}行：title（题干）不能为空")
            if not row["options"].strip():
                errors.append(f"第{row_num}行：options（选项）不能为空")
            else:
                opts = [o.strip() for o in row["options"].split("|") if o.strip()]
                if len(opts) < 2:
                    errors.append(f"第{row_num}行：选项至少需要2个（用 | 分隔）")
            # answer 校验
            ans_str = str(row["answer"]).strip()
            if not ans_str:
                errors.append(f"第{row_num}行：answer（答案）不能为空")

        if errors:
            st.error(f"数据校验不通过（共 {len(errors)} 处问题）：")
            for e in errors[:20]:
                st.warning(e)
            if len(errors) > 20:
                st.warning(f"...还有 {len(errors) - 20} 处问题")
            return

        # 导入按钮
        if st.button("✅ 确认导入", use_container_width=True, type="primary"):
            success_count = 0
            fail_count = 0
            with session_scope() as db:
                for idx, row in df.iterrows():
                    try:
                        qtype = row["type"].strip()
                        title = row["title"].strip()
                        options = [o.strip() for o in row["options"].split("|") if o.strip()]
                        ans_str = str(row["answer"]).strip()

                        # 解析答案
                        if qtype == "multi":
                            answer = [int(x.strip()) for x in ans_str.split("|")]
                        else:
                            answer = int(ans_str)

                        analysis = row.get("analysis", "").strip() if "analysis" in row else ""
                        category = row.get("category", "basic").strip() if "category" in row else "basic"
                        difficulty = row.get("difficulty", "normal").strip() if "difficulty" in row else "normal"
                        if difficulty not in ("easy", "normal", "hard"):
                            difficulty = "normal"

                        obj = Question(
                            type=qtype, title=title, options=options,
                            answer=answer, analysis=analysis,
                            category=category or "basic",
                            difficulty=difficulty,
                            is_active=True,
                        )
                        db.add(obj)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                db.commit()

            if fail_count == 0:
                st.success(f"🎉 批量导入完成！成功导入 {success_count} 道题目")
            else:
                st.warning(f"导入完成：成功 {success_count} 道，失败 {fail_count} 道")
            st.rerun()