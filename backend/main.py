from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app.api import api_router
from app.database.init_db import init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] 正在初始化数据库...")
    await init_db()
    print("[startup] 数据库初始化完成")
    yield


app = FastAPI(
    title=os.getenv("APP_NAME", "导游服务平台"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="导游服务平台后端API",
    lifespan=lifespan,
)

# CORS：支持 "*" 通配
allowed = os.getenv("ALLOWED_ORIGINS", "*").strip()
if allowed == "*" or allowed == "":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # 通配域不能开启凭证
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [o.strip() for o in allowed.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api")

# 静态文件：把 backend/uploads 目录挂到 /uploads
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "欢迎使用导游服务平台API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # 默认关闭 reload，避免 admin/ 文件改动或 windows 下 reload 子进程异常
    # 导致 8000 端口出现"半死"监听。如需开发热重载请设置环境变量 RELOAD=1
    enable_reload = os.getenv("RELOAD", "0").strip() == "1"
    port = int(os.getenv("PORT", "8000"))
    if enable_reload:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=["app"],
            reload_excludes=["admin/*", "uploads/*", "tests/*", "venv/*", ".venv/*"],
        )
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=port)