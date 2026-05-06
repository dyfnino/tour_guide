import asyncio
import aiomysql
import os
from dotenv import load_dotenv
from .session import async_engine, Base
from ..models import User, Course, Product, Live, Replay, AiTest, TestResult, Order, OrderItem

# 加载环境变量
load_dotenv()

# 从数据库URL中提取连接信息
def get_db_connection_info():
    db_url = os.getenv("DATABASE_URL", "mysql+aiomysql://root:@localhost:3306/guideshope")
    # 解析URL格式: mysql+aiomysql://user:password@host:port/dbname
    import re
    match = re.match(r"mysql\+aiomysql://(.*?):(.*?)@(.*?):(.*?)/(.*?)", db_url)
    if match:
        user, password, host, port, dbname = match.groups()
        return {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password,
            "db": dbname
        }
    else:
        # 默认值
        return {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "db": "guideshope"
        }

# 创建数据库（如果不存在）
async def create_database():
    conn_info = get_db_connection_info()
    db_name = conn_info.pop("db")
    
    try:
        # 连接到MySQL服务器
        async with aiomysql.connect(**conn_info, db="mysql") as conn:
            async with conn.cursor() as cur:
                # 检查数据库是否存在
                await cur.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
                result = await cur.fetchone()
                
                if not result:
                    # 创建数据库
                    await cur.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    print(f"数据库 {db_name} 创建成功")
                else:
                    print(f"数据库 {db_name} 已存在")
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        # 不抛出异常，让应用继续启动
        return

# 创建表结构
async def create_tables():
    try:
        async with async_engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        print("表结构创建成功")
    except Exception as e:
        print(f"创建表结构时出错: {e}")
        # 不抛出异常，让应用继续启动
        return

# 初始化数据库
async def init_db():
    print("开始初始化数据库...")
    
    try:
        # 创建数据库
        await create_database()
        
        # 创建表结构
        await create_tables()
        
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("应用将继续启动，但部分功能可能无法正常使用")

if __name__ == "__main__":
    asyncio.run(init_db())
