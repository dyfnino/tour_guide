# admin_backend 微信云托管部署说明

后台管理系统（Streamlit）独立容器化部署到微信云托管。

## 一、构建配置

- 构建目录：`admin_backend/`（在云托管新建服务时，「构建目录」填 `admin_backend`）
- Dockerfile 路径：`./Dockerfile`
- 监听端口：`80`（与云托管「版本配置 - 端口」保持一致）
- 健康检查：`/_stcore/health`

## 二、环境变量（在云托管「版本配置 - 环境变量」中填写）

| 变量                                                                           | 必填   | 说明                                                                                                             |
| ------------------------------------------------------------------------------ | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`                                                                 | 是     | 同步驱动串，格式 `mysql+pymysql://user:pwd@host:3306/db?charset=utf8mb4`；代码会自动把 `+aiomysql` 转 `+pymysql` |
| `ADMIN_USERNAME`                                                               | 是     | 后台登录账号                                                                                                     |
| `ADMIN_PASSWORD`                                                               | 是     | 后台登录密码                                                                                                     |
| `BACKEND_BASE_URL`                                                             | 是     | 上传资源对外访问域名（课程封面/视频 URL 前缀），指向 backend 服务域名                                            |
| `UPLOAD_DIR`                                                                   | 建议   | 容器内上传落地目录，默认 `/app/uploads`；容器实例销毁后文件会丢失，见下方「上传持久化」                          |
| `WX_PAY_MOCK`                                                                  | 否     | `1`=退款走 Mock（默认）；生产退款置 `0` 并配齐下列微信支付参数                                                   |
| `WX_PAY_APPID` / `WX_PAY_MCHID` / `WX_PAY_APIV3_KEY` / `WX_PAY_CERT_SERIAL_NO` | 视需要 | 真实退款时必填                                                                                                   |
| `WX_PAY_PRIVATE_KEY_PATH`                                                      | 视需要 | 商户私钥路径，默认 `/app/certs/apiclient_key.pem`                                                                |
| `WX_PAY_CERT_DIR`                                                              | 视需要 | 平台证书目录，默认 `/app/certs`（SDK 可自动下载）                                                                |
| `WX_PAY_NOTIFY_URL`                                                            | 视需要 | 退款/支付回调地址                                                                                                |

> 配置优先级：系统环境变量 > `admin_backend/.env` > `backend/.env`。
> 云托管注入的环境变量始终最高优先，`load_dotenv` 不会覆盖已存在变量。

## 三、上传持久化（重要）

`courses_page.py` 的文件上传默认写入容器内 `UPLOAD_DIR`。容器为无状态、缩容至 0 时本地文件会丢失，因此生产环境需二选一：

1. 挂载云托管「文件存储/NAS」到 `UPLOAD_DIR`，并让 backend 也挂载同一目录对外提供静态访问；
2. 改造为对象存储（COS）上传（后优化项）。

`BACKEND_BASE_URL` 必须指向真正能访问到这些文件的 backend 域名。

## 四、微信支付证书

如需真实退款，将 `apiclient_key.pem` 等证书通过以下任一方式提供到 `/app/certs`：

- 挂载文件存储到 `/app/certs`；
- 或在镜像内 COPY（注意 `.dockerignore` 已忽略 `certs/`，需按需调整）。
  仅做管理浏览、不涉及退款时，保持 `WX_PAY_MOCK=1` 即可，无需证书。

## 五、本地验证

```bash
cd admin_backend
pip install -r requirements.txt
streamlit run app.py            # 本地默认读 backend/.env
```

## 六、部署步骤

1. 微信云托管控制台 → 新建服务 → 选择「代码上传/Git」。
2. 构建目录填 `admin_backend`，Dockerfile 用仓库内 `./Dockerfile`。
3. 端口填 `80`，按需设置 CPU/内存（建议 0.5C/1G 起）。
4. 填写第二节环境变量。
5. 部署并分配流量，访问默认域名验证登录页。

## 七、常见问题

- **打不开/一直加载**：确认端口为 80，且 `enableCORS/enableXsrfProtection` 已关闭（见 `.streamlit/config.toml`）。
- **数据库连不上**：检查 `DATABASE_URL` 是否为 `pymysql` 驱动、云托管与 MySQL 网络是否互通。
- **上传后图片 404**：`BACKEND_BASE_URL` 或上传目录挂载不正确。
