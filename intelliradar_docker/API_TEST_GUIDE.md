# IntelliRadar API 测试指南

## 📋 目录
1. [基础测试](#基础测试)
2. [认证接口测试](#认证接口测试)
3. [威胁数据查询接口](#威胁数据查询接口)
4. [其他应用集成示例](#其他应用集成示例)

---

## 🌐 基础配置

```bash
# 本地测试地址
BASE_URL="http://localhost:8000"

# 或使用外网地址
# BASE_URL="http://27.54.47.51:6443"
```

---

## ✅ 基础测试

### 1. 健康检查
```bash
curl -X GET "$BASE_URL/api/health"
```

**预期返回**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T00:00:00Z"
}
```

### 2. 统计信息（无需登录）
```bash
curl -X GET "$BASE_URL/api/statistics"
```

**预期返回**:
```json
{
  "total_packages": 1234,
  "by_package_manager": {...},
  "by_confidence_level": {...},
  ...
}
```

---

## 🔐 认证接口测试

### 1. 用户注册
```bash
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456",
    "full_name": "Test User"
  }'
```

**预期返回**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": "..."
  }
}
```

### 2. 用户登录
```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123456"
```

**预期返回**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**保存 Token**:
```bash
# 将返回的 token 保存为变量
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. 获取当前用户信息
```bash
curl -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. 刷新 Token（滑动过期）
```bash
curl -X POST "$BASE_URL/api/auth/refresh" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 威胁数据查询接口

### 1. 获取威胁列表（分页）

#### 未登录访问（最多200条）
```bash
# 第1页，每页20条
curl -X GET "$BASE_URL/api/threats?page=1&page_size=20"

# 第10页（第200条），每页20条
curl -X GET "$BASE_URL/api/threats?page=10&page_size=20"

# 第11页会被拒绝（超过200条限制）
curl -X GET "$BASE_URL/api/threats?page=11&page_size=20"
```

#### 登录后访问（最多500条）
```bash
# 使用 Token 访问更多数据
curl -X GET "$BASE_URL/api/threats?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 可以访问到第25页（500条）
curl -X GET "$BASE_URL/api/threats?page=25&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

**预期返回**:
```json
{
  "threats": [
    {
      "threat_id": "...",
      "package_name": "malicious-pkg",
      "package_manager": "npm",
      "package_versions": ["1.0.0"],
      "threat_info": {...},
      "metadata": {...}
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 20,
  "total_pages": 25
}
```

### 2. 过滤查询

#### 按包管理器过滤
```bash
curl -X GET "$BASE_URL/api/threats?package_manager=npm&page=1&page_size=20"
```

#### 按威胁等级过滤
```bash
curl -X GET "$BASE_URL/api/threats?confidence_level=high&page=1&page_size=20"
```

#### 按数据源过滤
```bash
curl -X GET "$BASE_URL/api/threats?data_source=xmirror&page=1&page_size=20"
```

#### 组合过滤
```bash
curl -X GET "$BASE_URL/api/threats?package_manager=npm&confidence_level=high&data_source=osv&page=1&page_size=50"
```

#### 按包名搜索（模糊匹配）
```bash
curl -X GET "$BASE_URL/api/threats?package_name=lodash&page=1&page_size=20"
```

#### 按日期范围过滤
```bash
curl -X GET "$BASE_URL/api/threats?date_from=2025-01-01&date_to=2025-10-12&page=1&page_size=20"
```

### 3. 排序查询

#### 按更新时间降序（默认）
```bash
curl -X GET "$BASE_URL/api/threats?sort_by=metadata.last_updated&sort_order=desc&page=1&page_size=20"
```

#### 按包名升序
```bash
curl -X GET "$BASE_URL/api/threats?sort_by=package_name&sort_order=asc&page=1&page_size=20"
```

### 4. 获取最新威胁（固定10条）
```bash
curl -X GET "$BASE_URL/api/threats/latest"
```

**预期返回**:
```json
{
  "latest_packages": [
    {
      "id": "...",
      "package_name": "...",
      "package_manager": "npm",
      "version": ["1.0.0"],
      "collected_time": "2025-10-12T00:00:00Z",
      "confidence_level": "high"
    }
  ]
}
```

### 5. 获取威胁详情（通过ID）
```bash
# 替换 {threat_id} 为实际的威胁ID
curl -X GET "$BASE_URL/api/threats/{threat_id}"
```

### 6. 搜索威胁（POST）
```bash
curl -X POST "$BASE_URL/api/threats/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "lodash",
    "package_manager": "npm",
    "confidence_level": "high"
  }'
```

### 7. 查询包详情（供其他应用使用）⭐
```bash
# 查询特定包是否存在威胁
curl -X POST "$BASE_URL/api/packages/query" \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "lodash",
    "package_manager": "npm"
  }'

# 查询特定版本
curl -X POST "$BASE_URL/api/packages/query" \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "lodash",
    "package_manager": "npm",
    "package_versions": ["4.17.20"]
  }'
```

**使用场景**: CI/CD 流程中检查依赖是否有安全问题

---

## 🔧 其他应用集成示例

### Python 示例

#### 1. 基础查询
```python
import requests

BASE_URL = "http://localhost:8000"

# 查询包是否存在威胁
def check_package_security(package_name, package_manager, version=None):
    url = f"{BASE_URL}/api/packages/query"
    payload = {
        "package_name": package_name,
        "package_manager": package_manager
    }
    if version:
        payload["package_versions"] = [version]
    
    response = requests.post(url, json=payload)
    return response.json()

# 使用示例
result = check_package_security("lodash", "npm", "4.17.20")
if result:
    print(f"⚠️ 发现 {len(result)} 个安全威胁！")
else:
    print("✅ 该包安全")
```

#### 2. 带认证的查询
```python
import requests

class IntelliRadarClient:
    def __init__(self, base_url, email=None, password=None):
        self.base_url = base_url
        self.token = None
        if email and password:
            self.login(email, password)
    
    def login(self, email, password):
        """用户登录"""
        url = f"{self.base_url}/api/auth/login"
        data = {
            "username": email,
            "password": password
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False
    
    def get_threats(self, page=1, page_size=20, **filters):
        """获取威胁列表"""
        url = f"{self.base_url}/api/threats"
        params = {"page": page, "page_size": page_size, **filters}
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        response = requests.get(url, params=params, headers=headers)
        return response.json()
    
    def query_package(self, package_name, package_manager, versions=None):
        """查询包详情"""
        url = f"{self.base_url}/api/packages/query"
        payload = {
            "package_name": package_name,
            "package_manager": package_manager
        }
        if versions:
            payload["package_versions"] = versions
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

# 使用示例
client = IntelliRadarClient("http://localhost:8000")

# 未登录，最多查看200条
threats = client.get_threats(page=1, page_size=20, package_manager="npm")
print(f"找到 {len(threats['threats'])} 个威胁")

# 登录后，最多查看500条
client.login("test@example.com", "Test123456")
threats = client.get_threats(page=1, page_size=50, confidence_level="high")
print(f"高威胁等级: {len(threats['threats'])} 个")
```

### JavaScript/Node.js 示例

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

class IntelliRadarClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async login(email, password) {
    const url = `${this.baseUrl}/api/auth/login`;
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    
    const response = await axios.post(url, params);
    this.token = response.data.access_token;
    return this.token;
  }

  async getThreats(page = 1, pageSize = 20, filters = {}) {
    const url = `${this.baseUrl}/api/threats`;
    const params = { page, page_size: pageSize, ...filters };
    
    const headers = {};
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }
    
    const response = await axios.get(url, { params, headers });
    return response.data;
  }

  async queryPackage(packageName, packageManager, versions = null) {
    const url = `${this.baseUrl}/api/packages/query`;
    const data = {
      package_name: packageName,
      package_manager: packageManager
    };
    if (versions) {
      data.package_versions = versions;
    }
    
    const headers = {};
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }
    
    const response = await axios.post(url, data, { headers });
    return response.data;
  }
}

// 使用示例
(async () => {
  const client = new IntelliRadarClient(BASE_URL);
  
  // 查询包是否有威胁
  const threats = await client.queryPackage('lodash', 'npm', ['4.17.20']);
  if (threats.length > 0) {
    console.log(`⚠️ 发现 ${threats.length} 个安全威胁！`);
  } else {
    console.log('✅ 该包安全');
  }
})();
```

### Bash/Shell 脚本示例

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

# 函数: 检查包安全性
check_package() {
    local package_name=$1
    local package_manager=$2
    local version=$3
    
    echo "🔍 检查 $package_manager 包: $package_name@$version"
    
    if [ -z "$version" ]; then
        result=$(curl -s -X POST "$BASE_URL/api/packages/query" \
            -H "Content-Type: application/json" \
            -d "{\"package_name\":\"$package_name\",\"package_manager\":\"$package_manager\"}")
    else
        result=$(curl -s -X POST "$BASE_URL/api/packages/query" \
            -H "Content-Type: application/json" \
            -d "{\"package_name\":\"$package_name\",\"package_manager\":\"$package_manager\",\"package_versions\":[\"$version\"]}")
    fi
    
    # 检查是否返回空数组
    if [ "$result" = "[]" ]; then
        echo "✅ 安全 - 未发现威胁"
        return 0
    else
        echo "⚠️ 警告 - 发现安全威胁！"
        echo "$result" | jq '.[0].threat_info'
        return 1
    fi
}

# 使用示例
check_package "lodash" "npm" "4.17.20"
check_package "requests" "pypi"
```

---

## 🧪 完整测试脚本

创建文件 `test_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="Test123456"

echo "==================================="
echo "IntelliRadar API 完整测试"
echo "==================================="
echo ""

# 1. 健康检查
echo "1️⃣ 测试健康检查..."
curl -s "$BASE_URL/api/health" | jq
echo ""

# 2. 统计信息
echo "2️⃣ 测试统计信息..."
curl -s "$BASE_URL/api/statistics" | jq '.total_packages'
echo ""

# 3. 未登录查询（前200条）
echo "3️⃣ 测试未登录查询（第1页）..."
curl -s "$BASE_URL/api/threats?page=1&page_size=20" | jq '{total: .total, page: .page, count: (.threats | length)}'
echo ""

# 4. 用户登录
echo "4️⃣ 测试用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$EMAIL&password=$PASSWORD")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ 登录成功！"
    echo "Token: ${TOKEN:0:50}..."
else
    echo "❌ 登录失败，请先注册用户"
    exit 1
fi
echo ""

# 5. 登录后查询（前500条）
echo "5️⃣ 测试登录后查询..."
curl -s "$BASE_URL/api/threats?page=1&page_size=50" \
    -H "Authorization: Bearer $TOKEN" | jq '{total: .total, page: .page, count: (.threats | length)}'
echo ""

# 6. 测试过滤
echo "6️⃣ 测试过滤查询（npm包）..."
curl -s "$BASE_URL/api/threats?package_manager=npm&page=1&page_size=10" \
    -H "Authorization: Bearer $TOKEN" | jq '{total: .total, npm_count: (.threats | length)}'
echo ""

# 7. 测试包查询
echo "7️⃣ 测试包查询接口..."
curl -s -X POST "$BASE_URL/api/packages/query" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"package_name":"lodash","package_manager":"npm"}' | jq 'length'
echo ""

# 8. 测试最新威胁
echo "8️⃣ 测试获取最新威胁..."
curl -s "$BASE_URL/api/threats/latest" | jq '.latest_packages | length'
echo ""

echo "==================================="
echo "✅ 所有测试完成！"
echo "==================================="
```

**运行测试**:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 📊 API 限制说明

| 用户类型 | 最大数据量 | 每页最大条数 | Token有效期 |
|---------|----------|------------|-----------|
| 未登录 | 200条 | 100条 | - |
| 已登录 | 500条（可配置） | 100条 | 1小时（滑动） |

**滑动过期说明**: Token 有效期1小时，但每次调用 `/api/auth/refresh` 会刷新，只要用户持续使用就不会过期。

---

## 🔗 常见集成场景

### 1. CI/CD 集成
在 CI/CD 流程中检查依赖包安全性

### 2. IDE 插件
实时检查项目依赖的安全状态

### 3. 安全扫描工具
定期扫描项目依赖并生成报告

### 4. 监控告警系统
当发现新的威胁时自动告警

---

## 📞 需要帮助？

- API 文档: http://localhost:8000/api/docs
- 商务咨询: honywenair@163.com

