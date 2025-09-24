#!/bin/bash

# IntelliRadar 一键部署脚本
# 用于快速部署前后端和数据库，专注于测试功能而非数据采集

set -e  # 遇到错误立即退出

echo "🚀 IntelliRadar 一键部署启动..."
echo "====================================="

# 检查Docker和Docker Compose是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在包含 docker-compose.yml 的目录中运行此脚本"
    exit 1
fi

echo "✅ Docker 环境检查完成"

# 清理旧容器（如果存在）
echo "🧹 清理旧容器..."
docker-compose down --remove-orphans 2>/dev/null || true

# 构建镜像（使用缓存以提高速度）
echo "🔄 构建镜像..."
docker-compose build

# 启动所有服务
echo "🏗️  启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
echo "   正在等待 MongoDB 启动..."
sleep 15
echo "   正在等待后端服务启动..."
sleep 10
echo "   正在等待前端服务启动..."
sleep 5

# 检查服务状态
echo "📊 检查服务状态..."
echo "====================================="

# 检查MongoDB
echo "🗄️  检查 MongoDB..."
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    echo "✅ MongoDB 运行正常"
else
    echo "❌ MongoDB 启动失败"
fi

# 检查后端
echo "🔧 检查后端服务..."
sleep 5  # 给后端更多启动时间
if curl -f http://localhost:8000/api/health &> /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "⚠️  后端服务可能还在启动中，请稍后检查"
fi

# 检查前端
echo "🖥️  检查前端服务..."
if curl -f http://localhost:3000/health &> /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "⚠️  前端服务可能还在启动中，请稍后检查"
fi

echo "====================================="
echo "🎉 部署完成！"
echo ""
echo "📍 服务访问地址："
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/api/docs"
echo "   MongoDB:  mongodb://localhost:27017"
echo ""
echo "🔧 管理命令："
echo "   查看日志: docker-compose logs -f [service_name]"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart [service_name]"
echo ""
echo "📝 注意事项："
echo "   - 数据库已自动初始化威胁情报数据"
echo "   - 用户注册功能已启用"
echo "   - 数据采集功能已禁用（仅用于测试）"
echo ""
echo "✨ 开始使用 IntelliRadar 吧！"
