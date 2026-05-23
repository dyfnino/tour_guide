# 导游服务平台后端 API

基于 **Python 3.10+ / FastAPI / SQLAlchemy 2 / MySQL** 的异步后端服务，配套 `frontend/` 微信小程序使用。

## 数据库

- 引擎：MySQL（已安装并运行在 `localhost:3306`）
- 数据库名：`guide`（启动时若不存在会自动创建）
- 字符集：`utf8mb4`
- 默认用户：`root`，无密码

如需自定义连接，请编辑 [`backend/.env`](.env) 中的 `DATABASE_URL`。

## 启动

### Windows

```bash
cd backend
./start.bat
```

### Linux / macOS

```bash
cd backend
chmod +x start.sh
./start.sh
```

启动后：

- 服务地址：http://localhost:8000
- Swagger：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

首次启动会自动建库建表并写入种子数据（课程、题库、直播、回放、商品、AI 测评）。

## API 一览

### 鉴权 `/api/auth`

| 方法 | 路径    | 说明                                           |
| ---- | ------- | ---------------------------------------------- |
| POST | /wechat | 微信小程序登录（未配置 APPID 时走开发态 mock） |
| POST | /guest  | 游客登录，返回 token                           |
| GET  | /me     | 获取当前登录用户                               |
| PUT  | /me     | 更新昵称/头像/手机                             |

返回结构：`{ access_token, user }`。前端需将 `access_token` 存入本地，并在后续请求 `Authorization: Bearer <token>` 头中携带。

### 课程 `/api/courses`

- `GET /` 列表（支持 `category`）
- `GET /{id}` 详情
- `POST/PUT/DELETE` 管理接口

### 题库 / 考试

- `GET /api/questions` 题目列表（含答案，刷题用）
- `GET /api/questions/{id}` 单题
- `POST /api/exams/start` 开始考试，返回 `exam_id` + 抽到的题目（不含答案）
- `POST /api/exams/{exam_id}/submit` 交卷评分
- `GET /api/exams/{exam_id}` 查询考试结果

### 直播 `/api/live`

- `GET /lives` 直播列表 / `GET /lives/{id}` 直播详情
- `GET /replays` 回放列表 / `GET /replays/{id}` 回放详情
- `GET /lives/{id}/messages` 拉取最近消息
- `POST /lives/{id}/messages` 发送消息（已登录使用昵称，否则匿名）

### 商品 `/api/products`

- `GET /` 列表（支持 `category`、`is_new`、`is_hot`）
- `GET /{id}` 详情

### 我的（需登录）`/api/me`

- `GET /courses` 我的课程进度（仅 ID + progress）
- `GET /courses/detail` 我的课程列表（含课程详情，前端可直接渲染）
- `POST /courses/{course_id}/enroll` 加入学习
- `PUT /courses/{course_id}/progress` 更新进度

### 订单 `/api/orders`

现有 CRUD，未在本次范围调整。

### AI 测评 `/api/ai-test`

保留原有 CRUD（题目/结果），AI 模型对接为后续工作。

## 与前端约定

- 前端 [`frontend/utils/api.js`](../frontend/utils/api.js) 已封装上述接口。
- 默认基址 `http://localhost:8000/api`，开发者工具中需勾选「不校验合法域名」。
- 登录流程：
  1. 小程序调用 `wx.login` 拿到 `code`；
  2. 前端 `POST /api/auth/wechat { code }`；
  3. 收到 `access_token`，写入本地存储；
  4. 后续请求带 `Authorization: Bearer <token>`。

未配置 `WECHAT_APPID/WECHAT_SECRET` 时，后端使用 `dev_<code>` 当作 `openid` 自动建用户，方便本地联调。

## 目录结构

```
backend/
├── main.py
├── requirements.txt
├── .env
├── start.bat / start.sh
└── app/
    ├── api/         # FastAPI 路由
    │   ├── auth.py / users.py / courses.py / products.py
    │   ├── live.py / orders.py / ai_test.py
    │   ├── questions.py  (题库 + 考试)
    │   └── me.py         (个人中心：学习进度)
    ├── models/      # SQLAlchemy ORM
    ├── schemas/     # Pydantic v2
    ├── database/
    │   ├── session.py    (异步 engine)
    │   └── init_db.py    (建库 + 建表 + 种子数据)
    └── utils/
```

## 注意事项

1. 必须先保证本机 MySQL 已启动，root 用户具备建库权限。
2. 默认表使用 InnoDB + utf8mb4。
3. 题库表 `questions` / `exam_sessions` 使用 JSON 列，需 MySQL 5.7+ 支持。
4. CORS 默认 `*`，正式部署请改 `.env` 的 `ALLOWED_ORIGINS`。

## 后续计划

- 接入真实 AI 服务（DeepSeek 等）做导游词测评
- 接入支付能力（订单已有结构）
- WebSocket 直播间实时消息推送
- 文件上传 / 头像 OSS
