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
- 文件上传 / 头像OSS

---

## 微信云托管部署指南

### 一、前置准备

在部署前需要准备以下内容：

| 项目                             | 说明                                  |
| -------------------------------- | ------------------------------------- |
| 微信小程序 AppID                 | 微信公众平台注册                      |
| 微信小程序 AppSecret             | 微信公众平台 → 开发管理 → 开发设置    |
| MySQL 数据库                     | 云托管内网 MySQL 或腾讯云 CDB（推荐） |
| 微信支付商户号                   | 微信支付商户平台申请                  |
| 支付 APIv3 密钥                  | 商户平台 → API安全 → 设置APIv3密钥    |
| 商户私钥文件 (apiclient_key.pem) | 商户平台 → API安全 → 申请API证书      |
| 证书序列号                       | 下载证书后可查看                      |
| DashScope API Key（可选）        | 阿里云百炼平台申请，用于 AI 测评      |
| 备案域名                         | 用于微信支付回调通知                  |

### 二、项目文件结构（部署相关）

```
backend/
├── Dockerfile           # 微信云托管构建文件
├── entrypoint.sh        # 容器启动入口（含证书注入逻辑）
├── supervisord.conf     # 进程管理（同时运行 API + 管理后台）
├── .dockerignore        # 构建排除列表
├── requirements.txt     # Python 依赖
└── ...
```

### 三、部署步骤

#### 1. 开通微信云托管

- 登录 [微信云托管控制台](https://cloud.weixin.qq.com/)
- 创建环境，选择地域
- 创建 MySQL 数据库实例（记录内网地址、端口、用户名、密码）

#### 2. 创建服务

- 新建服务，选择「从代码构建」
- 代码根目录设为 `backend/`（Dockerfile 所在目录）
- 监听端口设为 **80**
- 如需访问管理后台，额外暴露端口 **8501**

#### 3. 配置环境变量

在云托管服务 → 「服务设置」→「环境变量」中添加以下配置：

**必需配置：**

```env
# ---- 数据库（使用云托管内网MySQL） ----
DATABASE_URL=mysql+aiomysql://root:你的数据库强密码@10.x.x.x:3306/guide?charset=utf8mb4

# ---- 应用 ----
DEBUG=False
SECRET_KEY=替换为32位以上高强度随机字符串
ALLOWED_ORIGINS=https://你的正式小程序域名,https://你的管理后台域名

# ---- 微信小程序 ----
WECHAT_APPID=你的小程序AppID
WECHAT_SECRET=你的小程序AppSecret

# ---- 管理后台 ----
ADMIN_USERNAME=admin
ADMIN_PASSWORD=设置一个强密码
```

**微信支付配置（需要支付功能时）：**

```env
WX_PAY_MOCK=0
WX_PAY_APPID=你的小程序AppID
WX_PAY_MCHID=你的商户号
WX_PAY_APIV3_KEY=你的APIv3密钥
WX_PAY_CERT_SERIAL_NO=商户证书序列号
WX_PAY_NOTIFY_URL=https://你的域名/api/orders/wechat/notify
# 可选：若不填，后端会基于 WX_PAY_NOTIFY_URL 自动推导为 /wechat/refund-notify
WX_PAY_REFUND_NOTIFY_URL=https://你的域名/api/orders/wechat/refund-notify

# 私钥内容（base64编码），entrypoint.sh 会自动解码写入文件
# 生成方法：在本地执行 base64 -w 0 certs/apiclient_key.pem 获取内容
WX_PAY_PRIVATE_KEY_CONTENT=私钥的base64编码内容
```

> **私钥 base64 编码方法：**
>
> - Linux/Mac: `cat certs/apiclient_key.pem | base64 -w 0`
> - Windows PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("certs\apiclient_key.pem"))`

**AI 测评配置（可选）：**

```env
DASHSCOPE_API_KEY=你的DashScope密钥
QWEN_MOCK=0
```

#### 4. 前端配置修改

部署后需修改小程序前端的 API 地址：

- `frontend/utils/api.js` 第4行：
  ```javascript
  const BASE_URL = "https://你的云托管域名/api";
  ```
- `frontend/app.js` 第23行：
  ```javascript
  apiBase: "https://你的云托管域名";
  ```

#### 5. 微信公众平台配置

登录 [微信公众平台](https://mp.weixin.qq.com/) → 开发管理 → 开发设置：

- **服务器域名 → request 合法域名**：添加 `https://你的云托管域名`
- **服务器域名 → uploadFile 合法域名**：添加 `https://你的云托管域名`（AI测评上传用）
- **服务器域名 → downloadFile 合法域名**：添加媒体文件 CDN 域名（如使用 OSS）

### 四、管理后台访问

管理后台（Streamlit）运行在容器的 8501 端口：

- **方案A**：在云托管中配置自定义路径，将 `/admin` 转发到 8501 端口
- **方案B**：额外创建一个服务专门运行管理后台（更安全，可单独配置鉴权）
- **方案C**：通过云托管的「端口转发」功能暴露 8501 端口

默认管理员账号：`admin` / `admin123`（请通过环境变量 `ADMIN_PASSWORD` 修改）

### 五、数据库初始化

首次部署启动时，系统会自动：

1. 检测并创建 `guide` 数据库
2. 创建所有表结构
3. 写入种子数据（示例课程、题库、商品等）

无需手动执行 SQL 迁移。

### 六、注意事项

1. **文件存储**：当前上传文件存储在容器本地 `/app/uploads/`，容器重建后会丢失。生产环境建议：
   - 使用云托管的 CFS 持久化存储挂载到 `/app/uploads`
   - 或接入腾讯云 COS 对象存储

2. **域名与 HTTPS**：微信云托管自动提供 HTTPS 域名，无需手动配置证书

3. **日志**：容器日志可在云托管控制台「日志管理」中查看

4. **扩缩容**：建议设置最小实例 1，最大实例按需配置。注意如果扩容到多实例，uploads 本地存储会不一致，此时必须接入对象存储

5. **TabBar 图标**：`frontend/app.json` 中 tabBar 未配置图标文件（iconPath/selectedIconPath），发布前需补充

6. **数据库备份**：建议开启云数据库的自动备份功能

### 七、生产上线前检查清单（详细版）

建议按「发布前 1 天」和「发布当天」两阶段执行，避免遗漏。

#### A. 发布前 1 天（配置与安全）

1. **环境变量去敏与生产化**
   - 禁止把真实密钥写入代码仓库，全部改为云托管环境变量。
   - 确保 `DEBUG=False`。
   - `SECRET_KEY` 使用 32 位以上高强随机值。
   - `ALLOWED_ORIGINS` 仅保留正式域名白名单（逗号分隔）。

2. **微信登录配置核对**
   - 配置正确的 `WECHAT_APPID` / `WECHAT_SECRET`。
   - 微信公众平台已添加 request / upload / download 合法域名。

3. **微信支付配置核对（必须）**
   - `WX_PAY_MOCK=0`（生产强制关闭 Mock）。
   - 回调地址使用：
     - 支付回调：`/api/orders/wechat/notify`
     - 退款回调：`/api/orders/wechat/refund-notify`
   - 商户号、APIv3 密钥、证书序列号已与商户平台一致。
   - `WX_PAY_PRIVATE_KEY_CONTENT` 为有效 base64，并可在容器启动时解码成功。

4. **数据库与存储准备**
   - 云数据库网络已放通（仅允许业务网段访问）。
   - 开启自动备份，确认备份周期与保留天数。
   - `/app/uploads/` 已挂载 CFS 或迁移到 COS（避免容器重建丢数据）。

5. **管理后台安全**
   - 修改默认管理员密码（禁止 `admin123`）。
   - 优先内网访问管理后台，或单独服务并加鉴权。

#### B. 发布当天（联调与回归）

1. **部署后健康检查**
   - 服务启动日志无报错。
   - API 首页、鉴权接口、下单接口可正常访问。

2. **支付全链路回归（真机）**
   - 微信登录 -> 下单 -> 拉起支付 -> 支付成功。
   - 支付回调能正确落库，订单状态由未支付变为已支付。

3. **退款链路回归**
   - 发起退款后，退款回调可达并正确更新订单退款状态。

4. **异常场景验证**
   - 非法签名回调应被拒绝。
   - 重复回调应幂等，不得重复记账。

5. **发布后观察（至少 30 分钟）**
   - 观察错误日志、支付失败率、接口耗时。
   - 如异常升高，按预案立即回滚到上一稳定版本。

#### C. 推荐回滚预案（最小集）

- 保留上一版本镜像 tag，确保可一键回退。
- 回滚时同步回退环境变量变更（若有）。
- 回滚后立即做一次登录、下单、支付冒烟验证。
