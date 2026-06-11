# ============================================================
# 导游服务平台 - 微信云托管 Dockerfile
# 同时运行 FastAPI 后端服务 (端口80) + Streamlit 管理后台 (端口8501)
# 微信云托管默认监听 80 端口
# ============================================================

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    PORT=80

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建上传目录
RUN mkdir -p /app/uploads/images /app/uploads/videos /app/uploads/audios

# 创建支付证书目录（部署时通过环境变量或挂载卷配置）
RUN mkdir -p /app/certs/wx_platform

# 复制启动脚本和 supervisor 配置
COPY entrypoint.sh /app/entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /app/entrypoint.sh

# 暴露端口：80 为主服务（微信云托管默认），8501 为管理后台
EXPOSE 80 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# 启动
CMD ["/app/entrypoint.sh"]