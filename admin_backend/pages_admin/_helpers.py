"""页面通用辅助函数。"""
import json
from typing import Any, List, Dict

import pandas as pd
import streamlit as st

from db import get_session


def query_to_df(query) -> pd.DataFrame:
    """SQLAlchemy 查询结果转 DataFrame。"""
    rows = query.all()
    if not rows:
        return pd.DataFrame()
    data: List[Dict[str, Any]] = []
    for r in rows:
        d = {}
        for c in r.__table__.columns:
            v = getattr(r, c.name)
            d[c.name] = v
        data.append(d)
    return pd.DataFrame(data)


def safe_json_loads(text: str, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def session_scope():
    return get_session()


def show_table(df: pd.DataFrame, height: int = 360):
    if df.empty:
        st.info("暂无数据")
        return
    st.dataframe(df, use_container_width=True, height=height)