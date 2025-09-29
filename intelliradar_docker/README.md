# IntelliRadar - Malicious Package Manager Component Threat Intelligence Database

IntelliRadar is a comprehensive threat intelligence platform that monitors and analyzes malicious components across major package managers. It provides real-time threat detection, intelligent analysis, and proactive security protection for software supply chains.

## 🚀 Features

### Core Capabilities
- **Real-time Threat Monitoring**: Continuous monitoring of malicious packages across multiple package managers
- **Intelligent Analysis**: Advanced threat analysis with confidence scoring and risk assessment
- **Multi-source Intelligence**: Aggregates data from 22+ authoritative security sources
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
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models.py       # Pydantic data models
│   │   ├── auth.py         # Authentication and authorization
│   │   └── database.py     # Database connection and queries
│   ├── crawler/            # Data collection and crawling
│   │   ├── base.py         # Base crawler classes
│   │   ├── content_extractor.py  # Content extraction logic
│   │   ├── pipeline.py     # Processing pipeline
│   │   ├── storage.py      # Data storage management
│   │   └── sources/        # Individual data source crawlers (22 sources)
│   ├── analysis/           # Threat analysis and processing
│   │   ├── intelligence_analyzer.py  # LLM-based threat analysis
│   │   └── intelligence_merger.py    # Data merging and deduplication
│   ├── database/           # Database management and schemas
│   │   ├── mongodb_manager.py     # MongoDB operations
│   │   ├── mongodb_schema.py      # Database schema definitions
│   │   ├── init-mongo.js          # Database initialization script
│   │   └── intelliradar/          # Database backup/initialization data
│   ├── configs/            # Configuration files
│   │   ├── llm_config.json        # LLM backend configuration
│   │   ├── crawler_config.py      # Crawler settings
│   │   └── config.py              # General application config
│   ├── utils/              # Utility functions
│   │   ├── llmquery.py            # LLM query utilities
│   │   └── time_utils.py          # Time handling utilities
│   ├── prompts/            # LLM prompts for analysis
│   ├── data/               # Collected threat intelligence data
│   │   ├── json/           # Structured JSON data from sources
│   │   ├── content/        # Raw content from sources
│   │   └── links/          # Discovered links
│   └── drivers/            # Web driver binaries (Chrome)
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   │   └── Navigation.jsx    # Main navigation component
│   │   ├── pages/          # Application pages
│   │   │   ├── HomePage.jsx      # Dashboard and overview
│   │   │   ├── Search.jsx        # Search functionality
│   │   │   ├── Statistics.jsx    # Statistics and analytics
│   │   │   ├── ThreatDatabase.jsx # Threat database listing
│   │   │   └── ThreatDetail.jsx  # Detailed threat view
│   │   └── services/       # API service layer
│   │       └── api.js            # API client functions
│   ├── nginx.conf          # Nginx configuration for production
│   └── Dockerfile          # Frontend container build
├── docker-compose.yml      # Container orchestration
├── deploy.sh               # One-click deployment script
└── intelliradar.yaml       # Kubernetes deployment config
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
- **Docker and Docker Compose** (Required)
- **Linux x86_64 architecture** (Recommended for production)
- **Git** (For cloning the repository)

### One-Click Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd /path/to/IntelliRadar/intelliradar_docker
   ```

2. **Set execution permissions and deploy**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:20002
   - Backend API: http://localhost:20001
   - API Documentation: http://localhost:20001/api/docs
   - MongoDB: mongodb://localhost:27017 (internal access only)

## ⚙️ LLM Configuration

The system supports multiple LLM backends for threat intelligence analysis. Configure the LLM settings in `/path/to/IntelliRadar/intelliradar_docker/backend/configs/llm_config.json`:

### Supported LLM Backends

#### 1. OpenAI API
```json
{
  "query_type": "openai",
  "reasoning_mode": false,
  "openai_api_model": "gpt-4.1",
  "openai_api_key": "your-openai-api-key",
  "default_max_tokens": 16000,
  "default_temperature": 0,
  "default_top_p": 0.3,
  "default_frequency_penalty": 0,
  "default_presence_penalty": 0,
  "default_seed": 42,
  "default_reasoning_effort": "medium",
  "default_extract_json": true,
  "auto_json_response": true
}
```

#### 2. Azure OpenAI
```json
{
  "query_type": "azure",
  "reasoning_mode": false,
  "azure_api_type": "azure",
  "azure_api_base": "https://your-resource.openai.azure.com/",
  "azure_api_model": "gpt-4.1",
  "azure_api_version": "2025-01-01-preview",
  "azure_api_key": "your-azure-api-key"
}
```

#### 3. Ollama (Local Deployment)
```json
{
  "query_type": "ollama",
  "reasoning_mode": false,
  "ollama_model": "gpt-oss:120b",
  "ollama_host": "127.0.0.1",
  "ollama_port": 11435,
  "ollama_context_size": 65536
}
```

#### 4. Xinference (Alternative Local Option)
```json
{
  "query_type": "xinference",
  "reasoning_mode": false,
  "xinference_model": "llama3",
  "xinference_api_base": "http://localhost:9997/v1",
  "xinference_api_key": "dummy-key"
}
```

### Embedding Configuration
The system also supports configurable embeddings for semantic search:
```json
{
  "embedding_backend": "openai",
  "embedding_model": "text-embedding-3-large",
  "embedding_dimension": 3072,
  "embedding_max_tokens": 8191
}
```

### Additional Configuration Parameters
The configuration file also includes advanced settings for fine-tuning LLM behavior:

```json
{
  "max_attempts": 5,
  "max_token_length": 16000,
  "retry_wait_time": 10,
  "retry_wait_increment": 5,
  "token_counting_model": "gpt-3.5-turbo-16k-0613",
  "token_slice_limit": 14000
}
```

### Important Configuration Notes

- **reasoning_mode**: Set to `true` if using reasoning models (o1-preview, o1-mini), otherwise `false`
- **query_type**: Choose from `"openai"`, `"azure"`, `"ollama"`, or `"xinference"`
- Update the corresponding API keys and endpoints for your chosen backend
- The system will automatically use the configured LLM for threat intelligence analysis
- **max_attempts**: Number of retry attempts for failed LLM queries
- **token_slice_limit**: Maximum tokens per request slice for large content processing

### Environment Variables

The system uses the following environment variables (automatically configured by docker-compose.yml):

```env
# Database Configuration
MONGODB_URL=mongodb://mongodb:27017
DATABASE_NAME=intelliradar
USER_DATABASE_NAME=intelliradar_users

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📊 API Documentation

### Core Endpoints

#### Authentication
- `POST /api/auth/register` - User registration with username, email, and password
- `POST /api/auth/login` - User login with OAuth2 password flow (returns JWT token)
- `GET /api/auth/me` - Get current authenticated user information

#### Health Check
- `GET /api/health` - Service health status with timestamp
- `GET /` - API information and documentation links

#### Statistics & Analytics
- `GET /api/statistics` - Platform statistics (total threats, package managers, confidence distribution)
- `GET /api/threats/latest` - Get latest 10 threat intelligence records

#### Threat Intelligence
- `GET /api/threats` - List threats with pagination, filtering, and sorting
  - Query parameters: `page`, `page_size`, `sort_by`, `sort_order`, `package_manager`, `confidence_level`, `package_name`, `data_source`, `date_from`, `date_to`
- `GET /api/threats/{threat_id}` - Get detailed threat intelligence by ID
- `POST /api/threats/search` - Advanced threat search with complex filters
- `POST /api/packages/query` - Query specific package details by name, manager, and optional version

#### Documentation
- `GET /api/docs` - Interactive Swagger UI documentation
- `GET /api/redoc` - ReDoc API documentation

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
- **Total Threats**: 39,702+ threat intelligence records
- **Package Managers**: npm (22,061), pypi (9,775), unknown (5,539), and more
- **Confidence Levels**: low (15,691), medium (13,620), high (10,391)
- **Data Sources**: 22+ authoritative security data sources

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

IntelliRadar aggregates threat intelligence from multiple authoritative sources:

- Security research organizations
- Package registry security advisories
- Open source intelligence feeds
- Community-contributed threat reports
- Automated malware detection systems

## 📊 Log Monitoring

### 📍 Log File Locations

After system startup, all log files are saved at the following locations:

- **Host Path**: `/path/to/IntelliRadar/intelliradar_docker/logs/` (logs folder in project root)
- **Container Path**: `/app/logs/`
- **Main Log Files**:
  - `crawler.log` - Threat intelligence collection logs
  - `api.log` - API access logs (if configured)
  - `error.log` - Error logs (if configured)

### 🔍 Log Monitoring Commands

#### Real-time Log Monitoring
```bash
# View latest collection logs in real-time
tail -f /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log

# Or view through container
docker exec intelliradar-backend tail -f /app/logs/crawler.log
```

#### View Historical Logs
```bash
# View last 50 lines of logs
tail -50 /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log

# View collection statistics
grep -E "(✓|completed successfully|discovered|content saved)" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log

# View error information
grep -E "(ERROR|✗|Failed)" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log

# View specific data source collection status
grep "reversinglabs" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log | tail -20
```

#### Log Analysis
```bash
# Count today's collections
grep "$(date +%Y-%m-%d)" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log | grep "Successfully processed" | wc -l

# View collection source statistics
grep "completed successfully" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log | awk '{print $4}' | sort | uniq -c

# View error statistics
grep "ERROR" /path/to/IntelliRadar/intelliradar_docker/logs/crawler.log | awk '{print $4}' | sort | uniq -c
```

### 📈 Crawler Status

#### View Crawler Process Status
```bash
# View collection-related processes
docker exec intelliradar-backend ps aux | grep python

# View cron job status
docker exec intelliradar-backend crontab -l
```

#### Crawler Configuration
- **Collection Frequency**: Every 6 hours (configurable)
- **Data Sources**: 22+ threat intelligence sources
- **Processing Mode**: Link discovery + Content processing + LLM analysis

## 🔧 Development

### Backend Development
```bash
cd /path/to/IntelliRadar/intelliradar_docker/backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd /path/to/IntelliRadar/intelliradar_docker/frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd /path/to/IntelliRadar/intelliradar_docker/backend
python -m pytest

# Frontend tests
cd /path/to/IntelliRadar/intelliradar_docker/frontend
npm test
```

## 🐳 Docker Configuration

### Service Architecture
The system consists of 4 main services defined in `/path/to/IntelliRadar/intelliradar_docker/docker-compose.yml`:

#### 1. MongoDB Database (`mongodb`)
- **Base Image**: mongo:7.0
- **Container**: intelliradar-mongodb
- **Port**: 27017 (internal), 27017 (external)
- **Health Check**: MongoDB ping command (`mongosh --eval "db.adminCommand('ping')"`)
- **Volumes**: 
  - `mongodb_data:/data/db` - Persistent data storage
  - `mongodb_logs:/var/log/mongodb` - Log storage
  - `./backend/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro` - Initialization script
  - `./backend/database/intelliradar:/backup/database/intelliradar:ro` - Database backup data
- **Environment**: `MONGO_INITDB_DATABASE=intelliradar`
- **Network**: intelliradar-network
- **Restart Policy**: unless-stopped

#### 2. Database Initialization (`db-init`)
- **Base Image**: mongo:7.0
- **Container**: intelliradar-db-init
- **Purpose**: One-time database initialization with threat intelligence data
- **Dependencies**: Waits for MongoDB to be healthy (`service_healthy`)
- **Command**: `["bash", "/init-db.sh"]`
- **Restart Policy**: "no" (runs only once)
- **Environment**: `MONGO_HOST=mongodb`

#### 3. Backend Service (`backend`)
- **Build Context**: ./backend with custom Dockerfile
- **Container**: intelliradar-backend
- **Port**: 8000 (internal), 20001 (external)
- **Health Check**: HTTP health endpoint at `http://localhost:8000/api/health`
- **Volumes**: `./logs:/app/logs` - Log files mounted to host
- **Environment Variables**:
  - `MONGODB_URL=mongodb://mongodb:27017`
  - `DATABASE_NAME=intelliradar`
  - `USER_DATABASE_NAME=intelliradar_users`
  - `SECRET_KEY=your-super-secret-key-change-this-in-production-2024`
  - `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- **Dependencies**: MongoDB healthy + db-init completed successfully
- **Restart Policy**: unless-stopped

#### 4. Frontend Service (`frontend`)
- **Build Context**: ./frontend with custom Dockerfile
- **Container**: intelliradar-frontend
- **Port**: 80 (internal), 20002 (external)
- **Build Args**: `REACT_APP_API_URL=http://4.5.3.12:20001`
- **Health Check**: HTTP health endpoint at `http://localhost/health`
- **Dependencies**: backend service
- **Restart Policy**: unless-stopped

### Network & Volumes
- **Network**: `intelliradar-network` (bridge driver)
- **Named Volumes**:
  - `intelliradar-mongodb-data` - MongoDB persistent data
  - `intelliradar-mongodb-logs` - MongoDB logs

## 🚀 Deployment Management

### Deploy Script Features
The `/path/to/IntelliRadar/intelliradar_docker/deploy.sh` script provides comprehensive one-click deployment:

#### Pre-deployment Checks
- ✅ Docker and Docker Compose installation verification
- ✅ Support for both Docker Compose V1 and V2
- ✅ Directory structure validation
- ✅ Linux x86_64 architecture optimization

#### Deployment Process
1. **Environment Setup**: Cleans up old containers and prepares environment
2. **Image Building**: Builds all service images with caching optimization
3. **Service Startup**: Launches all services with proper dependency ordering
4. **Health Verification**: Automated health checks for all services
5. **Crawler Initialization**: Starts threat intelligence collection service

#### Post-deployment Verification
- 🗄️ MongoDB connectivity test
- 🔧 Backend API health check
- 🖥️ Frontend service availability
- 🕷️ Automated crawler service startup

### Management Commands

#### Service Control
```bash
# View service status
docker-compose ps

# View service logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Stop and remove volumes (complete cleanup)
docker-compose down -v --remove-orphans
```

#### Log Monitoring
```bash
# View crawler logs
docker-compose logs -f backend

# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f mongodb
docker-compose logs -f frontend
```

#### Database Management
```bash
# Access MongoDB shell
docker exec -it intelliradar-mongodb mongosh

# Backup database
docker exec intelliradar-mongodb mongodump --out /backup

# View database status
docker exec intelliradar-mongodb mongosh --eval "db.stats()"
```

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