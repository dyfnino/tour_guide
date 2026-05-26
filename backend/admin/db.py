"""
后台管理用同步 SQLAlchemy 引擎 + 直接复用 FastAPI 的 ORM 模型。

注意：FastAPI 那边用的是异步引擎；Streamlit 用同步连接更直观，
两者共用同一张 MySQL 数据库，互不干扰。
"""
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv


# 让 admin 目录里的脚本能导入到 backend.app.models
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 加载 backend/.env
load_dotenv(BACKEND_DIR / ".env")


def _build_sync_url() -> str:
    """把 FastAPI 用的 mysql+aiomysql URL 转成同步 mysql+pymysql。"""
    raw = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://root:123456@localhost:3306/guide?charset=utf8mb4",
    )
    if "+aiomysql" in raw:
        raw = raw.replace("+aiomysql", "+pymysql")
    elif raw.startswith("mysql://"):
        raw = raw.replace("mysql://", "mysql+pymysql://", 1)
    return raw


SYNC_DATABASE_URL = _build_sync_url()
engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    return SessionLocal()


# 复用 FastAPI 的模型（一定要先 import models 包让 metadata 注册）
from app.models import (  # noqa: E402
    User, Course, Product, Live, Replay,
    AiTest,
    Question,
)
from app.models.question import ExamSession, UserCourse, LiveMessage  # noqa: E402
from app.models.ai_test import TestResult  # noqa: E402
from app.models.order import Order, OrderItem  # noqa: E402


def table_count(model) -> int:
    with get_session() as db:
        return db.query(model).count()


def safe_count(model) -> int:
    """对未建表的情况做容错，主要用于首次启动后台时数据库还未初始化的场景。"""
    try:
        return table_count(model)
    except Exception:
        return 0


__all__ = [
    "engine",
    "SessionLocal",
    "get_session",
    "table_count",
    "safe_count",
    # models
    "User", "Course", "Product", "Live", "Replay",
    "AiTest", "Question", "ExamSession", "UserCourse",
    "LiveMessage", "TestResult", "Order", "OrderItem",
]