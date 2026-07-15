# admin_backend 微信云托管部署配置清单（kk.md）

本文件详细罗列后台管理系统（Streamlit，`admin_backend`）部署到微信云托管所需的**全部配置项**。

---

## 一、代码仓库中已就绪的文件（无需手动改）

| 文件                     | 作用                                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| `Dockerfile`             | 构建镜像：python:3.11-slim + Streamlit 单服务，监听 **80** 端口                                   |
| `requirements.txt`       | 依赖：streamlit / sqlalchemy / pymysql / pandas / openpyxl / bcrypt / wechatpayv3 / python-dotenv |
| `.dockerignore`          | 构建时忽略 venv/.env/**pycache**/certs 等                                                         |
| `.streamlit/config.toml` | 端口 80、headless、关闭 CORS/XSRF、上传上限 500MB                                                 |
| `container.config.json`  | 端口/规格/环境变量模板                                                                            |
| `app.py`                 | 应用入口，云托管启动命令即 `streamlit run app.py`                                                 |

---

## 二、云托管「服务基础配置」

| 配置项            | 值                    | 说明                                          |
| ----------------- | --------------------- | --------------------------------------------- |
| 部署方式          | 代码上传 / Git 仓库   | 选自定义 Dockerfile                           |
| **构建目录**      | `admin_backend`       | 关键！必须指向该子目录，否则找不到 Dockerfile |
| Dockerfile 路径   | `./Dockerfile`        | 相对构建目录                                  |
| **监听端口**      | `80`                  | 必须与 Dockerfile/config.toml 一致            |
| 健康检查路径      | `/_stcore/health`     | Streamlit 内置健康端点                        |
| CPU / 内存        | 建议 0.5 核 / 1 GB 起 | 上传大文件时可提升                            |
| 最小 / 最大实例数 | 0 / 5（可调）         | 缩容至 0 可省成本，但会丢失容器内上传文件     |

---

## 三、环境变量（云托管「版本配置 → 环境变量」逐条填写）

### 3.1 必填

| 变量名             | 示例值                                                     | 说明                                                 |
| ------------------ | ---------------------------------------------------------- | ---------------------------------------------------- |
| `DATABASE_URL`     | `mysql+pymysql://user:pwd@host:3306/guide?charset=utf8mb4` | 数据库连接串；代码会自动把 `+aiomysql` 转 `+pymysql` |
| `ADMIN_USERNAME`   | `admin`                                                    | 后台登录账号                                         |
| `ADMIN_PASSWORD`   | `你的强密码`                                               | 后台登录密码                                         |
| `BACKEND_BASE_URL` | `https://backend-xxx.ap-shanghai.run.tcloudbase.com`       | 上传资源对外访问域名前缀，指向 backend 服务          |

### 3.2 上传相关（建议填）

| 变量名       | 示例值         | 说明                                                           |
| ------------ | -------------- | -------------------------------------------------------------- |
| `UPLOAD_DIR` | `/app/uploads` | 上传落地目录；容器无状态，需挂载持久卷，否则文件随实例销毁丢失 |

### 3.3 微信支付 / 退款（仅在后台需要真实退款时填）

| 变量名                    | 示例值                         | 说明                                       |
| ------------------------- | ------------------------------ | ------------------------------------------ |
| `WX_PAY_MOCK`             | `1`                            | `1`=Mock（默认，不退真钱）；真实退款置 `0` |
| `WX_PAY_APPID`            | `wx....`                       | 小程序 AppID                               |
| `WX_PAY_MCHID`            | `16xxxxxxxx`                   | 商户号                                     |
| `WX_PAY_APIV3_KEY`        | `32位密钥`                     | APIv3 密钥                                 |
| `WX_PAY_CERT_SERIAL_NO`   | `证书序列号`                   | 商户证书序列号                             |
| `WX_PAY_PRIVATE_KEY_PATH` | `/app/certs/apiclient_key.pem` | 商户私钥路径                               |
| `WX_PAY_CERT_DIR`         | `/app/certs/wx_platform`       | 平台证书目录（SDK 可自动下载）             |
| `WX_PAY_NOTIFY_URL`       | `https://.../notify`           | 回调地址                                   |

---

## 四、依赖的外部资源

| 资源         | 说明                                                               |
| ------------ | ------------------------------------------------------------------ |
| MySQL 数据库 | 云托管「数据库」或自建 MySQL；库表结构需与 backend 一致            |
| backend 服务 | 上传的图片/文件由 backend 提供访问，`BACKEND_BASE_URL` 必须可达    |
| 持久化存储   | 上传目录 `UPLOAD_DIR` 需挂载持久卷（NAS/CFS），否则实例重建后丢失  |
| 微信支付证书 | 仅真实退款需要，挂载到 `/app/certs`（构建被 `.dockerignore` 排除） |

---

## 五、上传文件持久化（重要）

容器为无状态，`UPLOAD_DIR` 默认目录内文件在实例销毁/缩容至 0 时会丢失。推荐方案：

1. **挂载持久卷**：在云托管为服务挂载 NAS/CFS 到 `UPLOAD_DIR`（如 `/app/uploads`），并与 backend 共享同一卷。
2. **对象存储 COS**：改造上传逻辑写入 COS，`BACKEND_BASE_URL` 指向 COS/CDN 域名（改动较大）。

最简做法：admin_backend 与 backend 挂载同一持久卷，`UPLOAD_DIR` 指向共享路径。

---

## 六、微信支付证书（仅真实退款需要）

- `.dockerignore` 已排除 `certs/`，证书**不打进镜像**。
- 真实退款时将证书通过持久卷挂载到 `/app/certs`：
  - 私钥 → `/app/certs/apiclient_key.pem`（对应 `WX_PAY_PRIVATE_KEY_PATH`）
  - 平台证书目录 → `/app/certs/wx_platform`（对应 `WX_PAY_CERT_DIR`）
- 不需要退款则保持 `WX_PAY_MOCK=1`，无需任何证书。

---

## 七、部署步骤

1. 代码推送到仓库（或打包上传）。
2. 云托管新建服务 → 选择「自定义 Dockerfile」。
3. **构建目录填 `admin_backend`**，Dockerfile 路径 `./Dockerfile`。
4. 监听端口填 `80`，健康检查路径 `/_stcore/health`。
5. 按第三章逐条填写环境变量。
6. （如需上传持久化/真实退款）挂载持久卷到 `/app/uploads`、`/app/certs`。
7. 构建并发布，等待健康检查通过。

---

## 八、验证与排错

| 现象                 | 排查方向                                                      |
| -------------------- | ------------------------------------------------------------- |
| 健康检查不通过       | 端口是否 80；`/_stcore/health` 是否可访问；查看构建/运行日志  |
| 登录失败             | `ADMIN_USERNAME` / `ADMIN_PASSWORD` 是否正确注入              |
| 数据库连接报错       | `DATABASE_URL` 格式、网络连通性、账号权限                     |
| 上传成功但图片打不开 | `BACKEND_BASE_URL` 是否指向可访问 backend；上传卷是否与其共享 |
| 上传文件重启后消失   | 未挂载持久卷；按第五章挂载 NAS/CFS 到 `UPLOAD_DIR`            |
| 退款报证书错误       | 证书是否挂载到 `/app/certs`；`WX_PAY_*` 是否配置齐全          |

---

本地验证：

```bash
cd admin_backend
streamlit run app.py --server.port=80
# 浏览器访问 http://localhost:80 ，用 ADMIN_USERNAME/ADMIN_PASSWORD 登录
```
