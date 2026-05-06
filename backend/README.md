# 导游服务平台后端API

## 项目简介

导游服务平台后端API是一个基于Python 3.12和FastAPI框架开发的异步后端服务，为微信小程序前端提供数据支持。

## 技术栈

- **Python**: 3.12
- **Web框架**: FastAPI (异步)
- **数据库**: MySQL (localhost:3306)
- **ORM**: SQLAlchemy 2.0 (异步)
- **依赖管理**: pip

## 项目结构

```
backend/
├── app/
│   ├── api/          # API接口
│   ├── models/       # 数据模型
│   ├── schemas/      # Pydantic模型
│   ├── database/     # 数据库配置
│   └── utils/        # 工具函数
├── main.py           # 主应用
├── requirements.txt  # 依赖文件
├── .env              # 环境变量
├── start.sh          # 启动脚本(Linux/macOS)
├── start.bat         # 启动脚本(Windows)
└── README.md         # 项目说明
```

## 数据库配置

- **主机**: localhost
- **端口**: 3306
- **数据库名**: guideshope
- **用户名**: root
- **密码**: (空)

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd backend
```

### 2. 启动服务

#### Windows系统

```bash
./start.bat
```

#### Linux/macOS系统

```bash
chmod +x start.sh
./start.sh
```

启动脚本会自动完成以下操作：
- 创建Python虚拟环境
- 激活虚拟环境
- 升级pip
- 安装依赖
- 初始化数据库
- 启动后端服务

## API接口

### 基础URL

```
http://localhost:8000/api
```

### 接口列表

#### 1. 课程相关

- `GET /api/courses` - 获取课程列表
- `GET /api/courses/{course_id}` - 获取课程详情
- `POST /api/courses` - 创建课程
- `PUT /api/courses/{course_id}` - 更新课程
- `DELETE /api/courses/{course_id}` - 删除课程

#### 2. 产品相关

- `GET /api/products` - 获取产品列表
- `GET /api/products/{product_id}` - 获取产品详情
- `POST /api/products` - 创建产品
- `PUT /api/products/{product_id}` - 更新产品
- `DELETE /api/products/{product_id}` - 删除产品

#### 3. 用户相关

- `GET /api/users` - 获取用户列表
- `GET /api/users/{user_id}` - 获取用户详情
- `POST /api/users` - 创建用户
- `PUT /api/users/{user_id}` - 更新用户
- `DELETE /api/users/{user_id}` - 删除用户

#### 4. 直播相关

- `GET /api/live/lives` - 获取直播列表
- `GET /api/live/lives/{live_id}` - 获取直播详情
- `POST /api/live/lives` - 创建直播
- `PUT /api/live/lives/{live_id}` - 更新直播
- `DELETE /api/live/lives/{live_id}` - 删除直播

- `GET /api/live/replays` - 获取回放列表
- `GET /api/live/replays/{replay_id}` - 获取回放详情
- `POST /api/live/replays` - 创建回放
- `PUT /api/live/replays/{replay_id}` - 更新回放
- `DELETE /api/live/replays/{replay_id}` - 删除回放

#### 5. AI测评相关

- `GET /api/ai-test/tests` - 获取测评列表
- `GET /api/ai-test/tests/{test_id}` - 获取测评详情
- `POST /api/ai-test/tests` - 创建测评
- `PUT /api/ai-test/tests/{test_id}` - 更新测评
- `DELETE /api/ai-test/tests/{test_id}` - 删除测评

- `GET /api/ai-test/results` - 获取测评结果列表
- `POST /api/ai-test/results` - 创建测评结果

## 数据库初始化

服务启动时会自动执行以下操作：
1. 检查数据库是否存在，不存在则创建
2. 创建所有表结构
3. 初始化基础数据

## 开发模式

服务默认以开发模式启动，支持热重载。

## 健康检查

可以通过以下接口检查服务状态：

```
GET http://localhost:8000/health
```

## API文档

FastAPI会自动生成API文档，可以通过以下地址访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 注意事项

1. 确保MySQL服务已启动
2. 确保MySQL用户root有创建数据库的权限
3. 首次启动时会自动创建数据库和表结构
4. 服务默认运行在8000端口

## 后续计划

1. 添加用户认证和授权
2. 实现文件上传功能
3. 集成AI模型API
4. 添加日志系统
5. 实现缓存机制
