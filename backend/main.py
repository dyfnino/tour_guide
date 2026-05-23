from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
async def root():
    return {"message": "欢迎使用导游服务平台API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)