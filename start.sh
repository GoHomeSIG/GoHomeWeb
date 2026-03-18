#!/bin/bash
# 思乡签到 - 快速启动脚本

echo "======================================"
echo "    思乡签到 - HomeSignin"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误：未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 安装后端依赖
echo "正在安装后端依赖..."
pip3 install -r requirements.txt

# 安装前端依赖
echo "正在安装前端依赖..."
cd frontend
npm install
cd ..

echo ""
echo "======================================"
echo "    依赖安装完成！"
echo "======================================"
echo ""
echo "启动方式："
echo ""
echo "1. 启动后端（终端 1）："
echo "   python3 app.py"
echo ""
echo "2. 启动前端（终端 2）："
echo "   cd frontend && npm run dev"
echo ""
echo "3. 访问应用：http://localhost:3000"
echo ""
