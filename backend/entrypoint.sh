#!/bin/bash
set -e

echo "[entrypoint] 导游服务平台启动中..."
echo "[entrypoint] API 服务端口: ${PORT:-80}"
echo "[entrypoint] 管理后台端口: 8501"

# 确保上传目录存在
mkdir -p /app/uploads/images /app/uploads/videos /app/uploads/audios

# ---- 微信支付证书：从环境变量注入文件 ----
# 在云托管环境变量中配置 WX_PAY_PRIVATE_KEY_CONTENT（base64编码的私钥内容）
if [ -n "$WX_PAY_PRIVATE_KEY_CONTENT" ]; then
    mkdir -p /app/certs/wx_platform
    echo "$WX_PAY_PRIVATE_KEY_CONTENT" | base64 -d > /app/certs/apiclient_key.pem
    chmod 600 /app/certs/apiclient_key.pem
    echo "[entrypoint] 微信支付私钥已写入 /app/certs/apiclient_key.pem"
    # 如果未显式设置路径，设置默认值
    export WX_PAY_PRIVATE_KEY_PATH=${WX_PAY_PRIVATE_KEY_PATH:-/app/certs/apiclient_key.pem}
    export WX_PAY_CERT_DIR=${WX_PAY_CERT_DIR:-/app/certs/wx_platform}
fi

# ---- DashScope API Key 检测 ----
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "[entrypoint] 警告: DASHSCOPE_API_KEY 未配置，AI测评将使用 Mock 模式"
fi

# 使用 supervisor 同时管理 FastAPI 和 Streamlit
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf