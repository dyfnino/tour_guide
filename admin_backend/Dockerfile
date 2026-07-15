# 导游服务平台 - 后台管理系统（Streamlit）独立容器
# 适配微信云托管：单服务监听 80 端口
FROM python:3.11-slim

# 环境变量：不生成 .pyc、日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖：pymysql 为纯 Python，无需 libmysqlclient；curl 用于健康检查
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖，利用层缓存
COPY requirements.txt /app/requirements.txt
RUN pip install --index-url https://mirrors.cloud.tencent.com/pypi/simple -r /app/requirements.txt

# 拷贝应用代码
COPY . /app

# 云托管默认监听 80 端口
EXPOSE 80

# 健康检查：命中 Streamlit 内置健康端点
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:80/_stcore/health || exit 1

# 启动 Streamlit（headless、监听所有网卡、80 端口）
CMD ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0", "--server.headless=true"]