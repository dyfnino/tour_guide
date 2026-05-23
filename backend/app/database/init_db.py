"""
数据库初始化：
1. 若 guide 数据库不存在则创建；
2. 创建所有表结构；
3. 写入种子数据（仅当对应表为空时）。
"""
import asyncio
import re
import os
import aiomysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import select

from .session import async_engine, Base, AsyncSessionLocal
from ..models import (
    User, Course, Product, Live, Replay,
    AiTest, Question,
)
from ..models.question import LiveMessage

load_dotenv()


def get_db_connection_info():
    db_url = os.getenv("DATABASE_URL", "mysql+aiomysql://root:@localhost:3306/guide")
    match = re.match(r"mysql\+aiomysql://(.*?):(.*?)@(.*?):(.*?)/(.*)", db_url)
    if match:
        user, password, host, port, dbname = match.groups()
        return {"host": host, "port": int(port), "user": user, "password": password, "db": dbname}
    return {"host": "localhost", "port": 3306, "user": "root", "password": "", "db": "guide"}


async def create_database():
    info = get_db_connection_info()
    db_name = info.pop("db")
    try:
        async with aiomysql.connect(**info, db="mysql") as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='{db_name}'"
                )
                if not await cur.fetchone():
                    await cur.execute(
                        f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                    print(f"[init_db] 数据库 {db_name} 创建成功")
                else:
                    print(f"[init_db] 数据库 {db_name} 已存在")
    except Exception as e:
        print(f"[init_db] 创建数据库失败: {e}")


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[init_db] 表结构创建完成")


# ---------- 种子数据 ----------

SEED_COURSES = [
    {
        "name": "导游基础知识精讲", "category": "basic", "image": "https://picsum.photos/300/180?random=1",
        "description": "36课时 | 适合零基础", "level": "李老师", "price": 0, "duration": 36, "is_free": True,
    },
    {
        "name": "导游业务能力提升", "category": "business", "image": "https://picsum.photos/300/180?random=2",
        "description": "24课时 | 进阶提升", "level": "王老师", "price": 99, "duration": 24,
    },
    {
        "name": "政策法规高频考点解析", "category": "policy", "image": "https://picsum.photos/300/180?random=7",
        "description": "12课时 | 考点精讲", "level": "赵老师", "price": 69, "duration": 12,
    },
    {
        "name": "地方导游基础知识", "category": "local", "image": "https://picsum.photos/300/180?random=8",
        "description": "20课时 | 实操讲解", "level": "钱老师", "price": 129, "duration": 20,
    },
]

SEED_PRODUCTS = [
    {"name": "手工特色糕点礼盒", "image": "https://picsum.photos/300/180?random=3", "price": 88, "category": "food", "is_hot": True, "stock": 200},
    {"name": "地方特色文创书签", "image": "https://picsum.photos/300/180?random=4", "price": 39, "category": "creative", "is_new": True, "stock": 500},
    {"name": "兵马俑纪念摆件", "image": "https://picsum.photos/300/180?random=21", "price": 168, "category": "creative", "stock": 80},
    {"name": "陕西特色干果礼盒", "image": "https://picsum.photos/300/180?random=22", "price": 56, "category": "food", "stock": 300},
]

SEED_QUESTIONS = [
    {"type": "single", "title": '中国第一部以"旅游"命名的法律是？',
     "options": ["《旅游法》", "《消费者权益保护法》", "《合同法》", "《民法典》"],
     "answer": 0, "category": "policy",
     "analysis": "《中华人民共和国旅游法》于2013年10月1日起施行。"},
    {"type": "single", "title": "导游人员的从业资格证是？",
     "options": ["导游证", "导游资格证", "从业资格证", "上岗证"],
     "answer": 1, "category": "basic",
     "analysis": "导游资格证是从事导游职业的资格凭证。"},
    {"type": "multi", "title": "以下属于世界文化遗产的有？（多选）",
     "options": ["秦始皇陵兵马俑", "黄山", "布达拉宫", "九寨沟"],
     "answer": [0, 2], "category": "basic",
     "analysis": "兵马俑、布达拉宫为文化遗产；黄山为双遗产；九寨沟为自然遗产。"},
    {"type": "judge", "title": "导游人员可在带团过程中擅自变更行程。",
     "options": ["正确", "错误"], "answer": 1, "category": "business",
     "analysis": "导游人员不得擅自变更接待计划。"},
    {"type": "single", "title": "大雁塔位于哪座城市？",
     "options": ["北京", "洛阳", "西安", "南京"], "answer": 2, "category": "local",
     "analysis": "大雁塔位于陕西省西安市。"},
    {"type": "single", "title": "下列哪项不是导游服务的基本要求？",
     "options": ["热情主动", "弄虚作假", "诚实守信", "讲解准确"], "answer": 1, "category": "business",
     "analysis": "导游服务应坚守诚信原则。"},
    {"type": "multi", "title": "下列哪些属于陕西名小吃？",
     "options": ["肉夹馍", "云吞", "羊肉泡馍", "凉皮"],
     "answer": [0, 2, 3], "category": "local",
     "analysis": "云吞为广东小吃。"},
    {"type": "judge", "title": "我国旅行社按经营范围分为出境社和国内社。",
     "options": ["正确", "错误"], "answer": 0, "category": "policy",
     "analysis": "我国旅行社分为出境游与国内游两大经营范围。"},
]

SEED_LIVES = [
    {
        "title": "导游资格证考试备考攻略",
        "description": "全面解析考点与备考策略",
        "lecturer": "张老师",
        "cover_image": "https://picsum.photos/800/400?random=12",
        "live_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "status": "live",
        "viewers": 1234,
    }
]

SEED_REPLAYS = [
    {"title": "导游基础知识精讲", "cover_image": "https://picsum.photos/300/180?random=13",
     "replay_url": "https://www.w3schools.com/html/mov_bbb.mp4", "duration": 5130, "views": 5678},
    {"title": "导游业务能力提升", "cover_image": "https://picsum.photos/300/180?random=14",
     "replay_url": "https://www.w3schools.com/html/mov_bbb.mp4", "duration": 3492, "views": 3456},
    {"title": "政策法规高频考点解析", "cover_image": "https://picsum.photos/300/180?random=15",
     "replay_url": "https://www.w3schools.com/html/mov_bbb.mp4", "duration": 4320, "views": 2345},
]

SEED_AI_TESTS = [
    {"name": "理论知识测评", "type": "theory", "difficulty": "normal", "duration": 30,
     "description": "考察导游基础理论知识"},
    {"name": "导游词讲解测评", "type": "lecture", "difficulty": "hard", "duration": 20,
     "description": "AI 评估您的导游词讲解水准"},
    {"name": "面试模拟测评", "type": "interview", "difficulty": "hard", "duration": 25,
     "description": "针对导游资格面试的模拟训练"},
]


async def seed_data():
    async with AsyncSessionLocal() as db:
        try:
            # 课程
            res = await db.execute(select(Course))
            if not res.scalars().first():
                for item in SEED_COURSES:
                    db.add(Course(**item))
                await db.commit()
                print("[seed] courses 写入完成")

            # 商品
            res = await db.execute(select(Product))
            if not res.scalars().first():
                for item in SEED_PRODUCTS:
                    db.add(Product(**item))
                await db.commit()
                print("[seed] products 写入完成")

            # 题库
            res = await db.execute(select(Question))
            if not res.scalars().first():
                for item in SEED_QUESTIONS:
                    db.add(Question(**item))
                await db.commit()
                print("[seed] questions 写入完成")

            # 直播
            res = await db.execute(select(Live))
            live_first = res.scalars().first()
            if not live_first:
                for item in SEED_LIVES:
                    db.add(Live(**item))
                await db.commit()
                # 取得新建直播 id 作为 replay 的 live_id
                res = await db.execute(select(Live))
                live_first = res.scalars().first()
                print("[seed] lives 写入完成")

            # 回放
            res = await db.execute(select(Replay))
            if not res.scalars().first() and live_first:
                for item in SEED_REPLAYS:
                    db.add(Replay(live_id=live_first.id, **item))
                await db.commit()
                print("[seed] replays 写入完成")

            # AI 测评
            res = await db.execute(select(AiTest))
            if not res.scalars().first():
                for item in SEED_AI_TESTS:
                    db.add(AiTest(**item))
                await db.commit()
                print("[seed] ai_tests 写入完成")

            # 直播间欢迎消息
            res = await db.execute(select(LiveMessage))
            if not res.scalars().first() and live_first:
                db.add(LiveMessage(live_id=live_first.id, nickname="系统",
                                   content="欢迎进入直播间，请文明发言。"))
                db.add(LiveMessage(live_id=live_first.id, nickname="小美",
                                   content="老师讲得真清楚！"))
                await db.commit()
                print("[seed] live_messages 写入完成")

        except Exception as e:
            print(f"[seed] 写入种子数据出错: {e}")
            await db.rollback()


async def init_db():
    print("[init_db] 开始初始化数据库...")
    try:
        await create_database()
        await create_tables()
        await seed_data()
        print("[init_db] 数据库初始化完成")
    except Exception as e:
        print(f"[init_db] 失败: {e}")


if __name__ == "__main__":
    asyncio.run(init_db())