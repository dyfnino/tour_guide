"""
测试用 FastAPI App 工厂：
- 用 SQLite 内存数据库（aiosqlite）替换 MySQL，避免依赖外部 DB
- 不调用 init_db.create_database / migrate_schema（那些是 MySQL 专属）
- 仅创建表 + 注册路由
- 强制 wechatpay/qwen 走 mock 模式，避免外部依赖
"""
import os
import sys
import asyncio
from pathlib import Path

# 让 backend 目录可被作为根加入 sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 强制 mock 模式
os.environ["WX_PAY_MOCK"] = "1"
os.environ["QWEN_MOCK"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

# 重要：在 import session 之前替换好 URL；session.py 在导入时构造 engine
# 但由于现有 session.py 使用 NullPool 加 sqlite 内存库会有连接隔离问题，
# 我们重新绑定一个共享 StaticPool 引擎。
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import session as db_session
from app.database.session import Base


# 重建一个共享内存引擎（StaticPool 让所有会话共享同一个 sqlite 内存连接）
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# 把 session 模块里的引擎和 Session 工厂换成 test 版
db_session.async_engine = test_engine
db_session.AsyncSessionLocal = TestSessionLocal


async def _override_get_db():
    async with TestSessionLocal() as s:
        try:
            yield s
        finally:
            await s.close()


# 触发模型 metadata 注册
from app import models  # noqa: F401
from app.models.question import LiveMessage  # noqa: F401
from app.models.ai_test import TestResult  # noqa: F401
from app.models.order import OrderItem  # noqa: F401


async def _create_all():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def build_app():
    """构造一个用于测试的 FastAPI 实例。"""
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from app.api import api_router
    from app.database.session import get_db

    app = FastAPI(title="test-app")
    app.include_router(api_router, prefix="/api")
    # 与生产环境保持一致：挂载 /uploads 静态文件
    uploads_dir = BACKEND_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    app.dependency_overrides[get_db] = _override_get_db
    return app


_loop = None


def run_async(coro):
    """同步上下文中跑一个协程，复用同一个 event loop。"""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)


def init_schema():
    """创建所有表。"""
    run_async(_create_all())


def get_session_factory():
    return TestSessionLocal