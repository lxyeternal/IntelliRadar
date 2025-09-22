# 🐳 IntelliRadar Docker 部署指南

## 📋 概述

IntelliRadar 现已完全 Docker 化，使用 MongoDB 替代本地文件存储，提供更好的扩展性和数据管理能力。

## 🏗️ 架构设计

```
🐳 Docker 容器架构
├── 🍃 MongoDB (数据库)
├── 🕷️ IntelliRadar Backend (爬虫服务)
├── 🌐 Mongo Express (数据库管理界面)
├── 📦 Redis (缓存，可选)
└── 🔒 Nginx (反向代理，可选)
```

## 🚀 快速启动

### 1. 准备环境

```bash
# 克隆项目
git clone <repository-url>
cd IntelliRadar

# 复制环境配置文件
cp env.example .env

# 编辑配置文件（可选）
nano .env
```

### 2. 启动服务

```bash
# 启动核心服务 (MongoDB + 爬虫)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f intelliradar-backend
```

### 3. 访问服务

- **MongoDB**: `localhost:27017`
- **Mongo Express**: `http://localhost:8081`
  - 用户名: `admin`
  - 密码: `intelliradar2024`

## 📊 MongoDB 数据结构

### 🔗 Links Collection
```javascript
{
  "_id": ObjectId,
  "timestamp": "20241201_143022_abc123",
  "source": "github",
  "url": "https://github.com/advisories/GHSA-xxxx",
  "post_date": "2024-12-01",
  "collected_at": "2024-12-01T14:30:22Z",
  "status": "processed",
  "has_content": true,
  "has_analysis": true,
  "structured_data": { ... }
}
```

### 📄 Content Collection
```javascript
{
  "_id": ObjectId,
  "timestamp": "20241201_143022_abc123",
  "source": "github", 
  "content": "网页内容...",
  "metadata": {
    "word_count": 1500,
    "has_tables": true,
    "has_code": false
  }
}
```

### 📋 Analysis Collection
```javascript
{
  "_id": ObjectId,
  "timestamp": "20241201_143022_abc123",
  "source": "github",
  "step": "extract",
  "step_number": 1,
  "result": { ... },
  "status": "success"
}
```

## 🛠️ 管理命令

### 查看数据统计
```bash
# 进入 MongoDB 容器
docker exec -it intelliradar-mongodb mongo -u admin -p intelliradar2024

# 查看数据库统计
use intelliradar
db.links.countDocuments()
db.content.countDocuments()
db.analysis.countDocuments()
```

### 重启爬虫服务
```bash
docker-compose restart intelliradar-backend
```

### 查看爬虫日志
```bash
docker-compose logs -f intelliradar-backend
```

### 备份数据库
```bash
# 创建备份
docker exec intelliradar-mongodb mongodump --uri="mongodb://admin:intelliradar2024@localhost:27017/intelliradar?authSource=admin" --out=/backup

# 复制备份文件到主机
docker cp intelliradar-mongodb:/backup ./mongodb-backup
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `MONGODB_URI` | MongoDB 连接字符串 | `mongodb://mongodb:27017/` |
| `MAX_WORKERS` | 并发爬虫数量 | `3` |
| `REQUEST_DELAY` | 请求间隔(秒) | `2` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | 空 |

### 数据持久化

数据通过 Docker volumes 持久化：
- `mongodb_data`: MongoDB 数据文件
- `crawler_logs`: 爬虫日志文件
- `redis_data`: Redis 数据文件

## 🔄 从文件存储迁移

如果你有现有的文件存储数据，可以使用迁移脚本：

```bash
# 运行迁移脚本（需要实现）
docker exec -it intelliradar-backend python scripts/migrate_file_to_mongodb.py
```

## 📈 监控和维护

### 健康检查
所有服务都配置了健康检查：
```bash
# 检查服务健康状态
docker-compose ps
```

### 性能监控
```bash
# MongoDB 性能统计
docker exec intelliradar-mongodb mongo --eval "db.serverStatus()"

# 容器资源使用
docker stats
```

## 🐛 故障排除

### 常见问题

1. **MongoDB 连接失败**
   ```bash
   # 检查 MongoDB 容器状态
   docker-compose logs mongodb
   
   # 重启 MongoDB
   docker-compose restart mongodb
   ```

2. **爬虫无法启动**
   ```bash
   # 检查 Chrome 依赖
   docker exec intelliradar-backend google-chrome --version
   
   # 查看详细错误日志
   docker-compose logs intelliradar-backend
   ```

3. **内存不足**
   ```bash
   # 增加 Docker 内存限制
   # 在 docker-compose.yml 中添加:
   deploy:
     resources:
       limits:
         memory: 2G
   ```

## 🔒 安全建议

1. **修改默认密码**
   ```bash
   # 修改 .env 文件中的密码
   MONGODB_PASSWORD=your_strong_password_here
   ```

2. **网络安全**
   - 生产环境中关闭不必要的端口
   - 使用 SSL/TLS 证书
   - 配置防火墙规则

3. **数据备份**
   - 定期备份 MongoDB 数据
   - 设置自动备份脚本

## 📚 更多资源

- [MongoDB 官方文档](https://docs.mongodb.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Chrome Headless 指南](https://developers.google.com/web/updates/2017/04/headless-chrome)

---

🎉 **恭喜！** 你的 IntelliRadar 现在已经完全 Docker 化并使用 MongoDB 存储数据了！
