# IntelliRadar - Malicious Package Manager Component Threat Intelligence Database

IntelliRadar is a comprehensive threat intelligence platform that monitors and analyzes malicious components across major package managers. It provides real-time threat detection, intelligent analysis, and proactive security protection for software supply chains.

## 🚀 Features

### Core Capabilities
- **Real-time Threat Monitoring**: Continuous monitoring of malicious packages across multiple package managers
- **Intelligent Analysis**: Advanced threat analysis with confidence scoring and risk assessment
- **Multi-source Intelligence**: Aggregates data from 19+ authoritative security sources
- **Advanced Search**: Multi-dimensional search capabilities with filtering and sorting
- **Statistical Analytics**: Comprehensive statistics and trend analysis
- **RESTful API**: Full-featured API for integration with external systems

### Supported Package Managers
- **NPM** (Node.js packages)
- **PyPI** (Python packages)
- **Maven** (Java packages)
- **NuGet** (.NET packages)
- **Cargo** (Rust packages)
- **RubyGems** (Ruby packages)

## 🏗️ Architecture

```
intelliradar_docker/
├── backend/                 # FastAPI backend service
│   ├── api/                # API endpoints and models
│   ├── crawler/            # Data collection and crawling
│   ├── analysis/           # Threat analysis and processing
│   ├── database/           # Database management and schemas
│   └── docker/             # Docker configuration files
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   └── services/       # API service layer
│   └── public/             # Static assets
└── docker-compose.yml      # Container orchestration
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT with bcrypt
- **Data Processing**: Custom threat analysis pipeline
- **Containerization**: Docker

### Frontend
- **Framework**: React 18
- **UI Library**: Ant Design
- **State Management**: React Query
- **Routing**: React Router
- **Styling**: CSS Modules + Ant Design
- **Charts**: Recharts
- **Animations**: Framer Motion

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IntelliRadar/intelliradar_docker
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=intelliradar
USER_DATABASE_NAME=intelliradar_users

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile

### Threat Intelligence Endpoints
- `GET /api/threats` - List threats with pagination and filtering
- `GET /api/threats/{id}` - Get threat details
- `POST /api/threats/search` - Advanced threat search
- `GET /api/statistics` - Get platform statistics

### Health Check
- `GET /api/health` - Service health status

## 🔍 Usage Examples

### Search for NPM Threats
```bash
curl -X POST "http://localhost:8000/api/threats/search" \
  -H "Content-Type: application/json" \
  -d '{
    "package_manager": "npm",
    "confidence_level": "high"
  }'
```

### Get Statistics
```bash
curl "http://localhost:8000/api/statistics"
```

## 🛡️ Security Features

- **JWT Authentication**: Secure user authentication and authorization
- **Input Validation**: Comprehensive input validation and sanitization
- **CORS Protection**: Configurable CORS policies
- **Rate Limiting**: API rate limiting to prevent abuse
- **Health Monitoring**: Continuous health checks and monitoring

## 📈 Data Sources

IntelliRadar aggregates threat intelligence from multiple authoritative sources:

- Security research organizations
- Package registry security advisories
- Open source intelligence feeds
- Community-contributed threat reports
- Automated malware detection systems

## 📊 日志监控

### 📍 日志文件位置

系统运行后，所有日志文件都会保存在以下位置：

- **宿主机路径**: `./logs/` (项目根目录下的 logs 文件夹)
- **容器内路径**: `/app/logs/`
- **主要日志文件**:
  - `crawler.log` - 威胁情报采集日志
  - `api.log` - API 访问日志 (如果配置)
  - `error.log` - 错误日志 (如果配置)

### 🔍 日志监控命令

#### 实时监控采集日志
```bash
# 实时查看最新采集日志
tail -f ./logs/crawler.log

# 或者通过容器查看
docker exec intelliradar-backend tail -f /app/logs/crawler.log
```

#### 查看历史日志
```bash
# 查看最近50行日志
tail -50 ./logs/crawler.log

# 查看采集统计信息
grep -E "(✓|completed successfully|discovered|content saved)" ./logs/crawler.log

# 查看错误信息
grep -E "(ERROR|✗|Failed)" ./logs/crawler.log

# 查看特定数据源的采集情况
grep "reversinglabs" ./logs/crawler.log | tail -20
```

#### 日志分析
```bash
# 统计今天的采集数量
grep "$(date +%Y-%m-%d)" ./logs/crawler.log | grep "Successfully processed" | wc -l

# 查看采集源统计
grep "completed successfully" ./logs/crawler.log | awk '{print $4}' | sort | uniq -c

# 查看错误统计
grep "ERROR" ./logs/crawler.log | awk '{print $4}' | sort | uniq -c
```

### 📈 采集程序状态

#### 查看采集进程状态
```bash
# 查看采集相关进程
docker exec intelliradar-backend ps aux | grep python

# 查看定时任务状态
docker exec intelliradar-backend crontab -l
```

#### 采集程序配置
- **采集频率**: 每12小时执行一次
- **数据源**: 19+ 个威胁情报源
- **处理模式**: 链接发现 + 内容处理 + LLM分析

## 🔧 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 🐳 Docker Configuration

### Backend Container
- **Base Image**: Python 3.11-slim
- **Service**: FastAPI application
- **Port**: 8000 (API)
- **Health Check**: HTTP health endpoint

### Database Container
- **Base Image**: MongoDB 7.0
- **Service**: MongoDB database
- **Port**: 27017 (MongoDB)
- **Health Check**: MongoDB ping command

### Frontend Container
- **Base Image**: Node.js + Nginx
- **Port**: 80 (served via Nginx)
- **Build**: Optimized production build

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [API Documentation](http://localhost:8000/api/docs)
- **Community**: [Discussions](https://github.com/your-repo/discussions)

## 🏆 Acknowledgments

- Security research community for threat intelligence
- Open source maintainers for package security tools
- Contributors to the threat detection algorithms

---

**IntelliRadar** - Protecting software supply chains through intelligent threat detection.
