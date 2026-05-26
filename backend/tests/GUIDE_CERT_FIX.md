# 导游考证三类接口加载失败 · 排查与修复

## 排查结论

经过实测，**后端三个接口本身都正常**（均返回 200）：

```
[OK] 网课点播 GET /courses -> 200
[OK] 网课点播 GET /courses?category=basic -> 200
[OK] 考试刷题 GET /questions?limit=50 -> 200
[OK] 考试刷题 GET /questions?category=basic -> 200
[OK] 模拟考试 微信登录 /auth/wechat -> 200
[OK] 模拟考试 POST /exams/start -> 200
```

**真实原因**：之前 8000 端口存在一个"半死"的旧后端进程（PID 监听着但不响应），表现为：

- `netstat -ano | findstr :8000` 显示一堆 CLOSE_WAIT
- 客户端请求 connection 能建立但 read 超时
- 这是 windows 上 uvicorn `reload=True` + WatchFiles 多进程退出异常造成的。

诱因：[`backend/main.py`](../main.py:62) 之前用 `uvicorn.run("main:app", ..., reload=True)`，当 `admin/`、`uploads/`、`tests/` 等目录文件变化时反复触发 reload，windows 下偶发 reload 失败但旧进程没清干净，端口"假活"。

## 已修复

### 1. main.py 改为默认不开 reload

修改 [`backend/main.py`](../main.py:62)：

```python
enable_reload = os.getenv("RELOAD", "0").strip() == "1"
if enable_reload:
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True,
        reload_dirs=["app"],
        reload_excludes=["admin/*", "uploads/*", "tests/*", "venv/*", ".venv/*"],
    )
else:
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

- 默认稳定模式：直接跑，不监听文件变化。
- 需要热重载时：`set RELOAD=1` 再启动。
- 即使开 reload，也只监听 `app/` 目录，admin/uploads/tests 不会触发重启。

### 2. 提供诊断脚本

[`backend/tests/diag_guide_cert.py`](diag_guide_cert.py) 是一键检测三类接口连通性的脚本：

```bash
cd backend
python tests/diag_guide_cert.py
```

## 之后如何启动后端（推荐流程）

```bash
# 1. 确保 MySQL 已启动（本项目读取 backend/.env 中的 DATABASE_URL，默认 root:123456@localhost:3306/guide）
# 2. 启动后端
cd backend
python main.py
# 看到 "Application startup complete." 即成功
```

## 如果仍然加载失败，按下面顺序排查

### 1. 确认后端在跑

浏览器打开 http://localhost:8000/health ，应返回 `{"status":"healthy"}`。

### 2. 跑诊断脚本

```bash
cd backend
python tests/diag_guide_cert.py
```

6 项全 OK 即表示后端没问题。

### 3. 小程序开发者工具检查

- 打开 **详情 → 本地设置 → 不校验合法域名/web-view**（用 localhost 必须勾选）
- 清缓存重新编译

### 4. 端口被旧进程占着但不响应

```cmd
netstat -ano | findstr :8000
```

如果出现大量 CLOSE_WAIT，找到 PID 用 `taskkill /F /PID <PID>` 杀掉后再重启 backend。

### 5. MySQL 没启动

```bash
python -c "import pymysql; c=pymysql.connect(host='localhost',port=3306,user='root',password='123456',database='guide',connect_timeout=3); print('OK')"
```

如果 timeout，先启 MySQL 服务。
