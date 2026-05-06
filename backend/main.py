from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.api import api_router
from app.database.init_db import init_db

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title=os.getenv("APP_NAME", "导游服务平台"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="导游服务平台后端API",
)

# 配置CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")

# 启动事件
@app.on_event("startup")
async def startup_event():
    print("正在初始化数据库...")
    await init_db()
    print("数据库初始化完成")

# 根路径
@app.get("/")
async def root():
    return {"message": "欢迎使用导游服务平台API"}

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
