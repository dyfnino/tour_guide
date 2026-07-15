"""
后台管理用同步 SQLAlchemy 引擎 + 本地 ORM 模型。

注意：FastAPI 那边用的是异步引擎；Streamlit 用同步连接更直观，
两者共用同一张 MySQL 数据库，互不干扰。
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 配置加载优先级：
# 1) 容器/云托管注入的系统环境变量（部署环境，最优先）
# 2) admin_backend/.env（独立部署时可自带）
# 3) backend/.env（本地开发且与 backend 同级时兜底）
# 说明：load_dotenv 默认不覆盖已存在的环境变量，因此云托管注入的变量始终生效。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOCAL_ENV = Path(__file__).resolve().parent / ".env"
_BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV)
if _BACKEND_ENV.exists():
    load_dotenv(_BACKEND_ENV)


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


# 导入本地模型（一定要先 import models 包让 metadata 注册）
from admin_app.models import (  # noqa: E402
    AiTest,
    Course,
    ExamSession,
    Live,
    LiveMessage,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Question,
    Refund,
    RefundStatus,
    Replay,
    TestResult,
    User,
    UserCourse,
)


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
    "engine", "SessionLocal", "get_session", "table_count", "safe_count",
    "User", "Course", "Product", "Live", "Replay",
    "AiTest", "Question", "ExamSession", "UserCourse",
    "LiveMessage", "TestResult", "Order", "OrderItem",
    "Refund", "RefundStatus", "OrderStatus",
]