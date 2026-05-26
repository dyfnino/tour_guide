# 导游服务平台微信小程序

## 项目简介

导游服务平台微信小程序是一个集导游考证、特产商城、直播课堂和AI测评为一体的综合性服务平台。

## 项目结构

```
├── app.json         # 小程序全局配置
├── app.js           # 小程序全局逻辑
├── app.wxss         # 小程序全局样式
├── pages/           # 页面目录
│   ├── home/        # 首页
│   ├── guide-cert/  # 导游考证
│   ├── specialty/   # 特产商城
│   ├── profile/     # 个人中心
│   ├── live/        # 直播课堂
│   └── ai-test/     # AI测评
├── components/      # 组件目录
├── utils/           # 工具函数目录
└── README.md        # 项目说明
```

## 功能模块

1. **首页**
   - 轮播图展示
   - 功能入口（导游考证、特产商城、直播课堂、AI测评）
   - 推荐课程
   - 热门特产

2. **导游考证**
   - 网课点播
   - 考试刷题
   - 模拟考试
   - 直播网课
   - AI测评

3. **特产商城**
   - 特色食品
   - 文创产品
   - 手工艺品
   - 地方特产

4. **个人中心**
   - 用户信息
   - 我的课程
   - 我的订单
   - 分销中心
   - 我的钱包
   - 设置
   - 帮助中心

5. **直播课堂**
   - 直播入口
   - 回放合集

6. **AI测评**
   - 理论知识测评
   - 导游词讲解测评
   - 面试模拟测评
   - AI对话助手

## 技术栈

- **前端框架**：微信小程序原生框架
- **后端服务**：待开发（计划使用Node.js + Express）
- **数据库**：MySQL（localhost:3306，数据库名：guide）
- **AI服务**：DeepSeek API（待集成）

## 开发环境

- **微信开发者工具**：最新版本
- **Node.js**：v16.0.0+
- **MySQL**：5.7+

## 运行项目

1. 克隆项目到本地
2. 打开微信开发者工具
3. 导入项目
4. 配置本地数据库连接
5. 运行项目

## 注意事项

1. 本项目为前端原型，后端服务和数据库连接需要另行配置
2. AI测评功能使用DeepSeek API，需要配置API Key
3. 直播功能需要集成第三方直播服务

## 后续计划

1. 开发后端服务
2. 集成数据库
3. 实现AI测评功能
4. 优化用户体验
5. 增加更多功能模块

---

## 微信小程序合法域名配置（重要）

小程序在「真机/体验版」必须配置合法域名，否则 wx.request / wx.downloadFile / video / audio 都会失败。
请在 微信公众平台 → 小程序后台 → 开发管理 → 开发设置 → 服务器域名 中配置：

- **request 合法域名**：后端 API 域名（HTTPS），例如 `https://api.your-domain.com`
- **socket 合法域名**：如使用 WebSocket
- **uploadFile 合法域名**：如使用 wx.uploadFile
- **downloadFile 合法域名**：视频/音频/图片的 CDN 域名，例如 `https://media.w3.org`、`https://your-cdn.com`

> 开发期间在微信开发者工具的「详情 → 本地设置」中可勾选「不校验合法域名」临时绕过，但发布前必须按上述配置。

### 后端 API 域名

`frontend/utils/api.js` 中的 `BASE_URL` 默认指向 `http://localhost:8000/api`，部署上线时请改为 HTTPS 域名。

### 媒体（视频/音频/图片）域名

- 课程播放使用 `<video>`/`<audio>`，资源 URL 必须来自已配置的 downloadFile 合法域名，且支持 HTTPS。
- 默认种子数据中的样例媒体（`media.w3.org`、`runoob.com`、`picsum.photos`）仅供本地联调，**生产环境务必替换为自有 CDN**（推荐：阿里云 OSS / 腾讯云 COS / 七牛云）。
- 替换方式：直接修改数据库 `courses.media_url` / `courses.image` 字段，或在 `backend/app/database/init_db.py` 的 `SEED_COURSES` 中改为自有 URL 后重新初始化。

## 微信支付配置

后端 `backend/.env` 提供以下支付相关变量：

```env
WX_PAY_MOCK=1                # 1=模拟支付（无需证书）；0=真实微信支付
WX_PAY_APPID=                # 小程序 AppID
WX_PAY_MCHID=                # 商户号
WX_PAY_V3_KEY=               # APIv3 密钥
WX_PAY_CERT_SERIAL=          # 商户证书序列号
WX_PAY_PRIVATE_KEY_PATH=     # 商户私钥文件路径（apiclient_key.pem）
WX_PAY_NOTIFY_URL=           # 回调地址（必须 HTTPS 公网可达）
```

- **本地联调**：保持 `WX_PAY_MOCK=1` 即可，前端会自动走 `/orders/{id}/mock-paid` 完成订单。
- **真实支付**：将 `WX_PAY_MOCK=0`，并填齐上述 6 项；`WX_PAY_NOTIFY_URL` 需要在「微信支付商户平台」白名单中。
