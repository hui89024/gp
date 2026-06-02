#!/bin/bash
# start.sh

echo "启动股票交易系统..."

# 启动数据库
echo "启动数据库服务..."
docker-compose up -d postgres redis

# 等待数据库就绪
sleep 5

# 启动后端
echo "启动后端服务..."
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "系统已启动！"
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:5173"
echo "API文档: http://localhost:8000/docs"

# 等待用户中断
wait $BACKEND_PID $FRONTEND_PID
