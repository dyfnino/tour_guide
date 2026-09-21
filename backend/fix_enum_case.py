"""一次性修复：把 orders/refunds 表里大写的枚举值转成小写，并统一 ENUM 列定义。

用法：
    cd backend
    ..\.venv\Scripts\python.exe fix_enum_case.py
"""
import os
import pymysql
from urllib.parse import urlparse, unquote

# 读取 .env 里的 DATABASE_URL
raw = "mysql+aiomysql://root:123456@localhost:3306/guide?charset=utf8mb4"
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                raw = line.split("=", 1)[1].strip()
                break

# 解析连接信息
u = urlparse(raw.split("?")[0].replace("+aiomysql", "").replace("+pymysql", ""))
conn = pymysql.connect(
    host=u.hostname or "localhost",
    port=u.port or 3306,
    user=unquote(u.username or "root"),
    password=unquote(u.password or ""),
    database=(u.path or "/guide").lstrip("/"),
    charset="utf8mb4",
)

SPECS = [
    ("orders", "status",
     ["unpaid", "paid", "completed", "refunding", "refunded", "cancelled"], "unpaid"),
    ("orders", "order_type", ["product", "course"], "product"),
    ("refunds", "status",
     ["pending", "processing", "success", "fail", "rejected", "closed"], "pending"),
]

try:
    with conn.cursor() as cur:
        for table, col, vals, default in SPECS:
            only = ",".join(f"'{v}'" for v in vals)
            # MySQL ENUM 大小写不敏感：直接 MODIFY 成小写标签，
            # 现有数据按「位置」映射到新标签，从而整体变为小写。
            cur.execute(
                f"ALTER TABLE {table} MODIFY {col} ENUM({only}) NOT NULL DEFAULT '{default}'")
            # 兜底：强制按小写值重写一遍，确保存储的就是小写字符串
            for v in vals:
                cur.execute(f"UPDATE {table} SET {col}=%s WHERE {col}=%s", (v, v))
            print(f"[fix] {table}.{col} 已统一为小写")
    conn.commit()
    print("[fix] 全部完成")
finally:
    conn.close()