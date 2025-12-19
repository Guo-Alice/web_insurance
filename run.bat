@echo off
echo 正在启动养老金规划系统...
echo 请确保已安装Python 3.7+

REM 创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 启动应用
echo 启动应用...
python app.py

pause
