#!/bin/bash

# ChainGuard 一键部署脚本
# 用于快速部署前后端和数据库，专注于测试功能而非数据采集

set -e  # 遇到错误立即退出

echo "🚀 ChainGuard 一键部署启动..."
echo "====================================="

# 检查Docker和Docker Compose是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose (支持 V1 和 V2)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 确定使用哪个 Docker Compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在包含 docker-compose.yml 的目录中运行此脚本"
    exit 1
fi

echo "✅ Docker 环境检查完成"

# 清理旧容器（如果存在）
echo "🧹 清理旧容器..."
$DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# 构建镜像（使用缓存以提高速度）
echo "🔄 构建镜像..."
$DOCKER_COMPOSE_CMD build

# 启动所有服务
echo "🏗️  启动服务..."
$DOCKER_COMPOSE_CMD up -d

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
if $DOCKER_COMPOSE_CMD exec -T mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    echo "✅ MongoDB 运行正常"
else
    echo "❌ MongoDB 启动失败"
fi

# 检查后端
echo "🔧 检查 ChainGuard-Intelliradar 服务..."
sleep 5  # 给后端更多启动时间
if curl -f http://localhost:20001/api/health &> /dev/null; then
    echo "✅ ChainGuard-Intelliradar 服务运行正常"
else
    echo "⚠️  ChainGuard-Intelliradar 服务可能还在启动中，请稍后检查"
fi

# 检查前端
echo "🖥️  检查前端服务..."
if curl -f http://localhost:443/health &> /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "⚠️  前端服务可能还在启动中，请稍后检查"
fi

# 启动定时采集任务
echo "🕷️  启动威胁情报定时采集服务..."
echo "   定时任务将在后台运行，每12小时自动采集一次"
$DOCKER_COMPOSE_CMD exec -d intelliradar bash /app/run_crawler.sh
sleep 2
echo "✅ 定时采集服务已启动"

echo "====================================="
echo "🎉 部署完成！"
echo ""
echo "📍 服务访问地址："
echo "   前端界面: https://27.54.47.51"
echo "   后端API:  http://27.54.47.51:20001"
echo "   API文档:  http://27.54.47.51:20001/api/docs"
echo "   MongoDB:  mongodb://localhost:27017 (仅内部访问)"
echo ""
echo "🔧 管理命令："
echo "   查看日志: $DOCKER_COMPOSE_CMD logs -f [service_name]"
echo "   停止服务: $DOCKER_COMPOSE_CMD down"
echo "   重启服务: $DOCKER_COMPOSE_CMD restart [service_name]"
echo "   查看采集日志: $DOCKER_COMPOSE_CMD logs -f intelliradar"
echo ""
echo "📝 注意事项："
echo "   - 数据库已自动初始化威胁情报数据"
echo "   - 用户注册功能已启用"
echo "   - 定时采集服务已启动（每12小时自动采集一次）"
echo "   - 首次采集将在部署完成后立即开始"
echo ""
echo "✨ 开始使用 ChainGuard 吧！"