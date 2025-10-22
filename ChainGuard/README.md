# ChainGuard - Malicious Package Manager Component Threat Intelligence Database

ChainGuard is a comprehensive threat intelligence platform that monitors and analyzes malicious components across major package managers. It provides real-time threat detection, intelligent analysis, and proactive security protection for software supply chains.

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
ChainGuard/
├── Intelliradar/           # FastAPI backend service
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

## 🌐 Network Configuration

### Port Architecture
ChainGuard uses a flexible network configuration that supports deployment on any server:

```
External Access:
├── Frontend (HTTPS): https://YOUR_SERVER_IP (Port 443)
├── Backend API: http://YOUR_SERVER_IP:20001
└── Database: Internal only (Port 27017)

Internal Container Network:
├── Frontend Container: nginx:80 → External:443
├── Backend Container: fastapi:8000 → External:20001
└── MongoDB Container: mongo:27017 → External:27017
```

### Key Network Features
- **Portable Configuration**: Uses relative API paths (`/api`) for maximum portability
- **Reverse Proxy**: Nginx automatically proxies `/api/*` requests to backend
- **CORS Enabled**: Supports cross-origin requests for development and production
- **SSL Ready**: Frontend serves on port 443 for HTTPS deployment

### Deployment Flexibility
The current configuration allows deployment on **any server** without code changes:
1. **Change Server IP**: Simply update `docker-compose.yml` ports if needed
2. **Different Ports**: Modify port mappings in `docker-compose.yml`
3. **Domain Names**: Works with both IP addresses and domain names
4. **Load Balancers**: Compatible with reverse proxies and load balancers

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
- Ports 443, 20001, and 27017 available

### Network Configuration for Different Servers

#### Option 1: Use Default Configuration (Recommended)
The current setup works on **any server** without modifications thanks to relative API paths:
```bash
# Clone and deploy - works on any IP address
git clone <repository-url>
cd ChainGuard
./deploy.sh
```
**Access URLs:**
- Frontend: `https://YOUR_SERVER_IP` (Port 443)
- Backend API: `http://YOUR_SERVER_IP:20001`
- API Docs: `http://YOUR_SERVER_IP:20001/api/docs`

#### Option 2: Custom Port Configuration
To use different ports, modify `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "YOUR_FRONTEND_PORT:80"  # Change 443 to your preferred port
Intelliradar:
  ports:
    - "YOUR_API_PORT:8000"     # Change 20001 to your preferred port
```

#### Option 3: Domain Name Setup
For domain names, the configuration works automatically:
```bash
# No code changes needed - just update DNS
# Access via: https://yourdomain.com and http://yourdomain.com:20001
```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intelliradar_docker
   ```

2. **Deploy using the automated script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
   
   Or manually:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: `https://YOUR_SERVER_IP` (Port 443)
   - Backend API: `http://YOUR_SERVER_IP:20001`
   - API Documentation: `http://YOUR_SERVER_IP:20001/api/docs`

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

### Core Endpoints

#### Health Check
- `GET /api/health` - Service health status
- `GET /` - API information and documentation links

#### Statistics & Analytics
- `GET /api/statistics` - Platform statistics (total threats, package managers, confidence distribution)
- `GET /api/threats/latest` - Get latest threat intelligence (10 most recent)

#### Threat Intelligence
- `GET /api/threats` - List threats with pagination and filtering
- `POST /api/packages/query` - Query specific package details by name and manager

#### Documentation
- `GET /api/docs` - Interactive Swagger UI documentation

### API Testing Results ✅

All API endpoints have been tested and are working correctly:

| Endpoint | Status | Response Time | Description |
|----------|--------|---------------|-------------|
| `GET /api/health` | ✅ | ~0.001s | Health check with timestamp |
| `GET /` | ✅ | ~0.001s | API info and docs link |
| `GET /api/statistics` | ✅ | ~0.296s | Complete platform statistics |
| `GET /api/threats/latest` | ✅ | ~0.096s | Latest 10 threat records |
| `GET /api/threats?limit=5` | ✅ | ~0.462s | Paginated threat list |
| `POST /api/packages/query` | ✅ | ~0.059s | Package-specific threat lookup |
| `GET /api/docs` | ✅ | ~0.002s | Swagger documentation UI |

### Database Statistics
- **Total Threats**: 39,702 威胁情报记录
- **Package Managers**: npm (22,061), pypi (9,775), unknown (5,539), 等
- **Confidence Levels**: low (15,691), medium (13,620), high (10,391)
- **Data Sources**: 19+ 权威安全数据源

## 🔍 Usage Examples

### Health Check
```bash
curl http://localhost:20001/api/health
# Response: {"status":"healthy","timestamp":"2025-09-28T16:27:12.524541+00:00"}
```

### Get Platform Statistics
```bash
curl http://localhost:20001/api/statistics
# Returns comprehensive statistics including threat counts, package manager distribution, etc.
```

### Get Latest Threats
```bash
curl http://localhost:20001/api/threats/latest
# Returns the 10 most recently discovered threats
```

### Query Specific Package
```bash
curl -X POST "http://localhost:20001/api/packages/query" \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "request", 
    "package_manager": "pypi"
  }'
# Example response shows malicious "request" package (typosquat of "requests")
```

### List Threats with Pagination
```bash
curl "http://localhost:20001/api/threats?limit=10&page=1"
# Returns paginated list of threats with full details
```

### Access Interactive API Documentation
```bash
# Open in browser:
http://localhost:20001/api/docs
# Provides Swagger UI for testing all endpoints
```

## 🛡️ Security Features

- **JWT Authentication**: Secure user authentication and authorization
- **Input Validation**: Comprehensive input validation and sanitization
- **CORS Protection**: Configurable CORS policies
- **Rate Limiting**: API rate limiting to prevent abuse
- **Health Monitoring**: Continuous health checks and monitoring

## 📈 Data Sources

ChainGuard aggregates threat intelligence from multiple authoritative sources:

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
docker exec ChainGuard-Intelliradar tail -f /app/logs/crawler.log
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
docker exec ChainGuard-Intelliradar ps aux | grep python

# 查看定时任务状态
docker exec ChainGuard-Intelliradar crontab -l
```

#### 采集程序配置
- **采集频率**: 每12小时执行一次
- **数据源**: 19+ 个威胁情报源
- **处理模式**: 链接发现 + 内容处理 + LLM分析

## 🌐 Network Configuration Details

### How the Portable Configuration Works

ChainGuard uses a **relative API path strategy** that makes it deployable on any server without code changes:

#### 1. Frontend Configuration
```javascript
// frontend/src/services/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api'
```

#### 2. Nginx Reverse Proxy
```nginx
# frontend/nginx.conf
location /api/ {
    proxy_pass http://Intelliradar:8000/;  # Proxies to backend container
}
```

#### 3. Docker Compose Setup
```yaml
frontend:
  build:
    args:
      - REACT_APP_API_URL=/api  # Uses relative path
  ports:
    - "443:80"  # External HTTPS port

Intelliradar:
  ports:
    - "20001:8000"  # External API port
```

### Network Flow
```
Browser Request: https://YOUR_SERVER_IP/api/statistics
       ↓
Nginx (Frontend): Matches /api/ location
       ↓
Proxy Pass: http://Intelliradar:8000/api/statistics
       ↓
FastAPI backend: Returns JSON data
```

### Troubleshooting Network Issues

#### Common Issues and Solutions

1. **Frontend shows "No Data" or API errors**
   ```bash
   # Check if backend is running
   curl http://YOUR_SERVER_IP:20001/api/health
   
   # Check container logs
   docker logs ChainGuard-Frontend
   docker logs ChainGuard-Intelliradar
   ```

2. **Port conflicts**
   ```bash
   # Check what's using your ports
   sudo netstat -tulpn | grep :443
   sudo netstat -tulpn | grep :20001
   
   # Modify docker-compose.yml if needed
   ```

3. **CORS errors in browser console**
   - The current configuration handles CORS automatically
   - Backend CORS settings are in `Intelliradar/api/main.py`

4. **SSL/HTTPS setup for production**
   ```bash
   # For production HTTPS with custom certificates:
   # 1. Add SSL certificates to nginx configuration
   # 2. Update nginx.conf to handle SSL termination
   # 3. Consider using nginx-proxy or Cloudflare
   ```

## 🔧 Development

### Backend Development
```bash
cd Intelliradar
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
cd Intelliradar
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

**ChainGuard** - Protecting software supply chains through intelligent threat detection.
