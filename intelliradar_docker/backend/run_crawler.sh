#!/bin/bash

# IntelliRadar 定时采集任务脚本
# 封装 main.py 的调用，支持定时运行

set -e

echo "🕷️  IntelliRadar 定时采集任务启动..."
echo "时间: $(date)"
echo "====================================="

# 进入后端目录
cd /app

# 设置 Python 路径
export PYTHONPATH=/app:$PYTHONPATH

# 运行定时采集任务（每6小时执行一次）
echo "🚀 启动定时威胁情报采集服务..."
python3 main.py schedule

echo "====================================="
echo "⚠️  定时采集服务已停止: $(date)"
echo ""
