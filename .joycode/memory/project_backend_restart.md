---
name: 后端配置修改需重启进程才生效
description: >-
  tour_guide 后端 FastAPI 通过 load_dotenv() 在启动时加载 .env；改 .env 或 py 代码后必须重启 uvicorn
  进程，否则运行中的旧进程仍用旧配置/旧代码
type: project
---

tour_guide 后端（backend/）是 FastAPI + uvicorn，通过 [backend/main.py](backend/main.py) 的 load_dotenv() 在**进程启动时**一次性加载 .env 环境变量。

**Why:** 曾出现"取消 AI 测评 mock 模式、已填 DASHSCOPE_API_KEY 并删除 qwen.py 里的 \_mock_reply()，但前端仍提示 '当前为 Mock 模式'"。根因是 8000 端口上运行中的后端进程仍是旧代码/旧环境变量，改动未重启不生效。

**How to apply:** 修改 backend/.env 或任何后端 .py 后，若用户反馈"改了没生效/还是旧行为"，优先怀疑进程未重启。排查：`netstat -ano | findstr :8000` 找 PID → `taskkill /PID <pid> /F` → `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000`。可用 curl 打 /api/ai-test/chat 验证 mock 字段为 false。
