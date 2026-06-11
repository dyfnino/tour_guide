# 导游服务平台（Tour Guide）

> 一个集**导游考证、特产商城、直播课堂、AI 测评**于一体的综合性服务平台，由「微信小程序前端 + FastAPI 后端 + Streamlit 后台管理」三端组成。

---

## 一、项目简介

本项目面向有考导游证、学习导游业务、采购地方特产等需求的用户，提供线上一体化的学习与交易场景：

- **学员端**：微信小程序，覆盖学习、刷题、考试、直播、AI 测评、商城下单、个人中心等完整业务闭环。
- **后端服务**：基于 FastAPI 提供 RESTful API、JWT 鉴权、微信登录、微信支付、文件上传、AI 多模态测评。
- **后台管理**：基于 Streamlit 搭建，与小程序共用同一 MySQL 数据库，运营人员可在线维护课程、题库、商品、订单、直播、用户。

---

## 二、整体架构

```
┌──────────────────┐      HTTPS / JSON      ┌──────────────────────┐
│ 微信小程序前端    │  ───────────────────▶  │ FastAPI 后端 (8000)   │
│ frontend/        │                        │ backend/main.py      │
└──────────────────┘                        └─────────┬────────────┘
                                                      │
┌──────────────────┐    SQLAlchemy / pymysql          │
│ Streamlit 后台   │  ─────────────────────────────▶  ▼
│ backend/admin/   │                        ┌──────────────────────┐
└──────────────────┘                        │   MySQL  (guide 库)  │
                                            └──────────────────────┘
                                                      ▲
                                            阿里 DashScope (Qwen 多模态)
                                            微信支付 V3
                                            微信小程序登录
```

---

## 三、项目结构

```
tour_guide/
├── frontend/                  # 微信小程序（原生框架）
│   ├── app.js / app.json / app.wxss
│   ├── pages/
│   │   ├── home/              # 首页
│   │   ├── login/             # 微信/游客登录
│   │   ├── guide-cert/        # 导游考证（课程/刷题/模考）
│   │   ├── specialty/         # 特产商城
│   │   ├── live/              # 直播 + 回放
│   │   ├── ai-test/           # AI 多模态测评
│   │   └── profile/           # 个人中心（订单/课程）
│   ├── utils/api.js           # 后端 API 封装
│   └── project.config.json
│
├── backend/                   # FastAPI 后端服务
│   ├── main.py                # 入口（含 lifespan 自动建库）
│   ├── requirements.txt
│   ├── .env                   # 数据库/微信/支付/AI 配置
│   ├── start.bat / start.sh
│   ├── start_admin.bat        # 启动 Streamlit 后台
│   ├── app/
│   │   ├── api/               # 路由：auth/courses/questions/exams/
│   │   │                       #       live/products/orders/me/ai_test/users
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── schemas/           # Pydantic v2
│   │   ├── database/          # 引擎 + 建表 + 种子数据
│   │   └── utils/             # JWT / 微信 / 支付 / AI 客户端
│   ├── admin/                 # Streamlit 后台管理
│   │   ├── app.py             # 后台入口（侧边栏导航）
│   │   ├── auth.py / db.py
│   │   └── pages_admin/       # 课程/题库/商品/订单/直播/回放/用户/AI
│   ├── uploads/               # 用户上传的图片/音频（静态目录）
│   └── tests/
│
├── README.md                  # 本文件
└── .gitignore
```

---

## 四、功能模块

### 小程序端

| 模块         | 功能                                                                               |
| ------------ | ---------------------------------------------------------------------------------- |
| **首页**     | 轮播图、4 大功能入口、推荐课程、热门特产                                           |
| **导游考证** | 视频/音频网课、刷题（单选/多选/判断）、模拟考试（自动评分）、直播网课、AI 测评入口 |
| **特产商城** | 特色食品 / 文创产品 / 手工艺品 / 地方特产，支持新品 / 热销筛选，下单 + 微信支付    |
| **直播课堂** | 直播间（聊天消息）、回放列表（最新优先，下拉刷新 + 触底分页）                      |
| **AI 测评**  | 理论知识 / 导游词讲解 / 面试模拟 / AI 对话，支持图片+音频+文本多模态               |
| **个人中心** | 微信/游客登录、我的课程进度、订单列表与详情、分销中心、钱包、设置                  |

### 后台管理（Streamlit）

控制台 / 课程 / 题库 / 商品 / 直播 / 回放 / AI 测评 / 订单 / 用户 共 9 大模块，所有变更对小程序立即生效。

---

## 五、技术栈

| 端     | 技术                                                              |
| ------ | ----------------------------------------------------------------- |
| 小程序 | 微信小程序原生框架（WXML / WXSS / JS）                            |
| 后端   | Python 3.10+、FastAPI 0.104、SQLAlchemy 2、aiomysql、Pydantic v2  |
| 数据库 | MySQL 5.7+（默认 `localhost:3306/guide`，utf8mb4，使用 JSON 列）  |
| 鉴权   | JWT（python-jose）+ bcrypt                                        |
| 支付   | 微信支付 V3（wechatpayv3 1.3.7），支持 mock 模式                  |
| AI     | 阿里云 DashScope（Qwen Plus / VL-Max / Audio-Turbo / Omni-Turbo） |
| 后台   | Streamlit + pymysql + pandas                                      |

---

## 六、快速启动

### 1. 准备环境

- Python 3.10+
- MySQL 5.7+（已启动在 `localhost:3306`，root 用户具备建库权限）
- 微信开发者工具（最新版）

### 2. 启动后端

**Windows：**

```bash
cd backend
./start.bat
```

**Linux / macOS：**

```bash
cd backend
chmod +x start.sh
./start.sh
```

启动后：

- 服务地址：<http://localhost:8000>
- Swagger 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

> 首次启动会自动建库建表并写入种子数据（课程、题库、直播、回放、商品、AI 测评）。

### 3. 启动后台管理

```bash
cd backend
streamlit run admin/app.py
# 或 Windows 双击 start_admin.bat
```

浏览器自动打开 <http://localhost:8501>。

- 默认账号：`admin` / `admin123`
- 可通过 `backend/.env` 中的 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 覆盖。

### 4. 启动小程序

1. 打开微信开发者工具
2. 导入 `frontend/` 目录
3. 「详情 → 本地设置」勾选「不校验合法域名」（仅本地开发）
4. 编译预览即可

---

## 七、关键配置（backend/.env）

```env
# 数据库
DATABASE_URL=mysql+aiomysql://root:@localhost:3306/guide?charset=utf8mb4

# CORS（生产环境改为具体域名）
ALLOWED_ORIGINS=*

# 微信小程序登录（未配置则使用 dev_<code> mock）
WECHAT_APPID=
WECHAT_SECRET=

# 微信支付
WX_PAY_MOCK=1                # 1=模拟支付；0=真实支付
WX_PAY_APPID=
WX_PAY_MCHID=
WX_PAY_V3_KEY=
WX_PAY_CERT_SERIAL=
WX_PAY_PRIVATE_KEY_PATH=
WX_PAY_NOTIFY_URL=

# AI 测评（阿里 Qwen 多模态，未配置自动 mock）
DASHSCOPE_API_KEY=
QWEN_MOCK=0
QWEN_TEXT_MODEL=qwen-plus
QWEN_VL_MODEL=qwen-vl-max
QWEN_AUDIO_MODEL=qwen-audio-turbo
QWEN_OMNI_MODEL=qwen-omni-turbo

# 后台管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 八、API 一览

完整接口请参考 [`backend/README.md`](backend/README.md:1) 或 Swagger。常用分组：

| 前缀             | 模块                               |
| ---------------- | ---------------------------------- |
| `/api/auth`      | 微信/游客登录、当前用户信息        |
| `/api/courses`   | 课程列表、详情、增删改             |
| `/api/questions` | 题库（刷题）                       |
| `/api/exams`     | 考试开始 / 交卷评分                |
| `/api/live`      | 直播 / 回放 / 聊天消息             |
| `/api/products`  | 商品列表与详情                     |
| `/api/orders`    | 订单创建 / 支付 / 退款 / mock 回调 |
| `/api/me`        | 我的课程 + 进度                    |
| `/api/ai-test`   | 多模态测评（上传 + 对话）          |
| `/uploads/*`     | 用户上传文件静态访问               |

前端 API 封装位于 [`frontend/utils/api.js`](frontend/utils/api.js:1)，默认 `BASE_URL = http://localhost:8000/api`，上线请改为 HTTPS 域名。

---

## 九、微信小程序合法域名

发布前必须在 「微信公众平台 → 开发管理 → 服务器域名」 中配置：

| 类型                  | 用途                 |
| --------------------- | -------------------- |
| request 合法域名      | 后端 API（HTTPS）    |
| uploadFile 合法域名   | AI 测评上传图片/音频 |
| downloadFile 合法域名 | 视频/音频/图片 CDN   |
| socket 合法域名       | 若使用 WebSocket     |

> 默认种子数据中的 `media.w3.org` / `picsum.photos` 仅供本地联调，**生产环境务必替换为自有 CDN**（OSS / COS / 七牛）。

---

## 十、AI 测评接口

- `POST /api/ai-test/upload`：表单上传图片/音频，返回 `{path, url}`
- `POST /api/ai-test/chat`：多模态对话
  - body：`{message, image_paths[], audio_paths[], image_urls[], audio_urls[], history[]}`
- `POST /api/ai-test/evaluate`：理论 / 讲解 / 面试 测评
  - body：`{test_type: "theory|lecture|interview", topic, user_answer, image_paths, audio_paths, ...}`
  - 模型按 JSON 输出 `{score, feedback, suggestions}`
- `GET /api/ai-test/files/{name}`：访问已上传的临时文件

未配置 `DASHSCOPE_API_KEY` 时自动降级 mock，不会让前端报错。

---

## 十一、退款流程

订单退款采用**用户申请 → 后台审核 → 微信发起 → 异步回调**的标准链路，支持全额 / 部分退款，可多次退款（累计 ≤ 订单总额）。

### 订单状态机

```
unpaid ──支付──▶ paid ──申请退款──▶ refunding ──退款成功──▶ refunded（全额）
   │                │                     │              │
   │                │                     │              └─部分退款 ▶ paid
   │                │                     └─审核拒绝 ▶ paid
   ├─用户取消 ▶ cancelled
   └─确认收货 ▶ completed ──申请退款──▶ refunding（同上）
```

### 接口（前端 / 用户侧）

- `POST /api/orders/{order_id}/refund`：用户申请退款
  - body: `{reason: "原因", amount: 可选(元)}`，不传 amount 即全额退款
  - 创建一条 `pending` 退款单，订单状态 → `refunding`
- `GET  /api/orders/{order_id}/refunds`：查看本订单全部退款记录
- `POST /api/orders/{order_id}/mock-refunded`：仅 Mock 模式，把待处理退款单一键置为成功

### 接口（后台 / 管理员）

- `GET  /api/orders/refunds/all?refund_status=pending`：列出全部退款单
- `POST /api/orders/refunds/{refund_id}/review`：审核
  - body: `{approve: true/false, admin_remark: ""}`
  - 通过 → 提交微信，回调或同步成功后扣减订单 `refunded_amount`
  - 拒绝 → 关闭退款单，订单恢复 `paid`
- `POST /api/orders/refunds/{refund_id}/query`：主动查询微信侧状态（同步用）
- `POST /api/orders/wechat/refund-notify`：微信退款异步回调入口

### 微信支付配置（追加）

`backend/.env`：

```env
# 退款回调地址（可选；不填则从 WX_PAY_NOTIFY_URL 推导为同前缀的 /refund-notify）
WX_PAY_REFUND_NOTIFY_URL=https://api.your-domain.com/api/orders/wechat/refund-notify
```

### Streamlit 后台

- 「订单管理 → 退款审核」Tab：查看待审核队列，逐条**通过/拒绝**
- 「订单管理 → 订单详情」：可对已支付订单**直接发起退款**（绕过用户申请）

### 业务影响

- **课程订单全额退款** → 自动从 `user_courses` 移除该课程（用户失去学习权限）
- **商品订单**仅做资金返回，**不**自动恢复库存（如需可在 [`_apply_refund_success`](backend/app/api/orders.py:1) 内补充）
- **部分退款**：`refunded_amount` 累计；剩余金额仍可继续退款
- **幂等**：同一退款单多次回调只生效一次，订单 `refunded_amount` 不会重复累加

---

## 十二、注意事项

1. 必须先启动 MySQL，root 用户具备建库权限。
2. 题库表 `questions` / `exam_sessions` 使用 JSON 列，需 **MySQL 5.7+**。
3. 后台所有变更对小程序立即生效（共享同一 MySQL）。
4. 订单总金额不允许在后台直接修改，仅能切换状态；如需调金额请走业务退款流程（见第十一章）。
5. 用户表不允许修改 `username`，避免与登录态冲突。
6. CORS 默认 `*`，正式部署请改 `.env` 的 `ALLOWED_ORIGINS` 为具体域名。
7. 媒体文件（视频/音频/封面）放在自有 CDN，并在小程序后台配置 downloadFile 合法域名。

---

## 十三、后续规划

- [ ] WebSocket 直播间实时消息推送
- [ ] 头像 / 课程封面接入 OSS
- [ ] 分销与佣金体系完整化
- [ ] 优惠券 / 拼团 / 秒杀
- [ ] App / H5 端复用同一后端

---

## 许可证

本项目仅供学习交流使用。
