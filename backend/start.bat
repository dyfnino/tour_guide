@echo off

rem 启动脚本

rem 创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

rem 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

rem 升级pip
echo 升级pip...
pip install --upgrade pip

rem 安装依赖
echo 安装依赖...
pip install -r requirements.txt

rem 启动服务
echo 启动后端服务...
python main.py
