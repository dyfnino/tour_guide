#!/bin/bash
set -e

echo "[entrypoint] 导游服务平台启动中..."
echo "[entrypoint] API 服务端口: ${PORT:-80}"
echo "[entrypoint] 管理后台端口: 8501"

# 确保上传目录存在
mkdir -p /app/uploads/images /app/uploads/videos /app/uploads/audios

# 使用 supervisor 同时管理 FastAPI 和 Streamlit
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf