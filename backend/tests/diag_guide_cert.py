"""
导游考证三类接口连通性诊断脚本。
依赖运行中的后端：默认 http://localhost:8000

用法：
    python tests/diag_guide_cert.py
"""
import sys
import requests

BASE = "http://localhost:8000/api"


def show(name, r):
    tag = "[OK]" if r.ok else "[FAIL]"
    print(f"{tag} {name} -> {r.status_code}")
    if not r.ok:
        print("   ", r.text[:300])


def main():
    # 1) 网课点播
    show("网课点播 GET /courses", requests.get(BASE + "/courses", timeout=5))
    show("网课点播 GET /courses?category=basic", requests.get(BASE + "/courses?category=basic", timeout=5))

    # 2) 考试刷题
    show("考试刷题 GET /questions?limit=50", requests.get(BASE + "/questions?limit=50", timeout=5))
    show("考试刷题 GET /questions?category=basic", requests.get(BASE + "/questions?category=basic", timeout=5))

    # 3) 模拟考试（要登录）
    r = requests.post(BASE + "/auth/wechat", json={"code": "diagtest", "nickName": "diag"}, timeout=5)
    show("模拟考试 微信登录 /auth/wechat", r)
    if r.ok:
        tok = r.json()["access_token"]
        h = {"Authorization": "Bearer " + tok}
        show("模拟考试 POST /exams/start", requests.post(BASE + "/exams/start", headers=h, json={"count": 10, "duration": 3600}, timeout=8))


if __name__ == "__main__":
    main()