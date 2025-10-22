# ChainGuard Database Structure Documentation

## Overview

**Database Name:** `intelliradar`

**Database Type:** MongoDB 7.0

**Total Collections:** 7

**Total Documents:** 295,726

**Total Data Size:** 252.5 MB

**Total Storage Size:** 81.5 MB

**Total Index Size:** 24.3 MB

---

## Collections Summary

| Collection | Documents | Purpose |
|------------|-----------|---------|
| `threat_intelligence` | 40,531 | Merged threat intelligence data from all sources |
| `analysis` | 217,567 | Analysis results from content extraction pipeline |
| `links` | 28,867 | Discovered links from crawlers |
| `content` | 8,755 | Extracted content from collected links |
| `pipeline_tasks` | 3 | Pipeline execution logs and statistics |
| `users` | 1 | User accounts for authentication |
| `login_history` | 2 | User login records |

---

## 1. threat_intelligence Collection

**Purpose:** Stores merged and deduplicated threat intelligence data from multiple security sources.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  id: String,                       // Custom unique ID (format: IR-YYYYMMDD-manager-hash)
  package_name: String,             // Name of the affected package
  package_manager: String,          // Package manager (pypi, npm, maven, nuget, gem, go)
  package_versions: Array<String>,  // List of affected versions
  repository_url: Array<String>,    // Related repository URLs
  
  credit: {
    sources: Array<{
      discoverer: String | Array<String>, // Person/organization who discovered the threat
      data_source: String,                 // Source platform name
      discovery_date: ISODate,             // Discovery timestamp
      source_link: String                  // Original source URL
    }>,
    collected_at: ISODate              // Collection timestamp
  },
  
  references: Array<{
    url: String,                     // Reference URL
    type: String                     // Reference type/source
  }>,
  
  threat_info: {
    attack_methods: Array<String>,   // Attack techniques used
    attack_vectors: Array<String>,   // Attack entry points
    targets: Array<String>           // Affected targets/platforms
  },
  
  patch_info: {
    fix_method: String               // Remediation instructions
  },
  
  indicators_of_compromise: Array<String>, // IOCs (suspicious files, URLs, behaviors)
  
  metadata: {
    created_at: ISODate,             // First creation time
    last_updated: ISODate,           // Last update time
    data_quality_score: Number,      // Quality score (0-1)
    confidence_level: String         // Confidence level (high, medium, low)
  }
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `id_1` | `id: 1` | Unique | Ensure unique threat IDs |
| `package_name_1` | `package_name: 1` | Standard | Search by package name |
| `package_manager_1` | `package_manager: 1` | Standard | Filter by package manager |
| `metadata.last_updated_-1` | `metadata.last_updated: -1` | Descending | Sort by update time |
| `metadata.confidence_level_1` | `metadata.confidence_level: 1` | Standard | Filter by confidence |

### Example Query

```javascript
// Get all high-confidence PyPI threats updated in the last 7 days
db.threat_intelligence.find({
  package_manager: "pypi",
  "metadata.confidence_level": "high",
  "metadata.last_updated": { $gte: new Date(Date.now() - 7*24*60*60*1000) }
}).sort({ "metadata.last_updated": -1 })
```

---

## 2. users Collection

**Purpose:** Stores user account information for authentication and authorization.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  username: String,                 // Username (lowercase, unique)
  email: String,                    // Email address (lowercase, unique)
  full_name: String,                // User's full name (optional)
  hashed_password: String,          // Bcrypt hashed password
  is_active: Boolean,               // Account active status
  created_at: ISODate,              // Account creation time
  view_limit: Number,               // Data viewing limit (default: 500)
  last_login: ISODate               // Last login timestamp
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |

### Security Features

- **Password Hashing:** Bcrypt with 12 rounds
- **JWT Authentication:** Access tokens with configurable expiration
- **Access Control:** 
  - Unauthenticated users: 200 items limit
  - Authenticated users: Configurable limit (default 500)
  - Admin users: Unlimited access (future feature)

### Example Query

```javascript
// Find user by email
db.users.findOne({ email: "user@example.com" })

// Update last login time
db.users.updateOne(
  { username: "user@example.com" },
  { $set: { last_login: new Date() } }
)
```

---

## 3. login_history Collection

**Purpose:** Records user login history for security auditing and analytics.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  username: String,                 // Username (lowercase)
  login_time: ISODate,              // Login timestamp
  ip_address: String,               // Client IP address
  user_agent: String                // Browser user agent string
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `username_1` | `username: 1` | Standard | Query by username |
| `login_time_1` | `login_time: 1` | Standard | Sort by time |

### Use Cases

- Security monitoring and anomaly detection
- User behavior analytics
- Compliance and audit trails
- Geographic access pattern analysis

### Example Query

```javascript
// Get all login history for a user
db.login_history.find({ username: "user@example.com" })
  .sort({ login_time: -1 })
  .limit(10)

// Find recent logins from suspicious IPs
db.login_history.find({
  login_time: { $gte: new Date(Date.now() - 24*60*60*1000) },
  ip_address: { $in: ["suspicious.ip.1", "suspicious.ip.2"] }
})
```

---

## 4. pipeline_tasks Collection

**Purpose:** Tracks pipeline execution history, performance metrics, and source-level statistics.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  task_id: String,                  // Unique task ID (format: task_YYYYMMDD_HHMMSS_random)
  task_type: String,                // Task type (scheduled, manual, api)
  trigger_source: String,           // Trigger source (cron, user, api)
  start_time: ISODate,              // Task start time
  end_time: ISODate,                // Task completion time
  status: String,                   // Task status (running, completed, failed)
  workers: Number,                  // Number of parallel workers
  sources_to_run: Array<String> | null, // Specific sources to run (null = all)
  
  total_sources: Number,            // Total sources processed
  success_sources: Number,          // Successfully processed sources
  failed_sources: Number,           // Failed sources
  total_duration: Number,           // Total execution time (seconds)
  
  source_results: Array<{
    source: String,                 // Source name
    status: String,                 // Source execution status
    start_time: ISODate | null,     // Source start time
    end_time: ISODate | null,       // Source end time
    links_discovered: Number,       // Links discovered in link stage
    links_processed: Number,        // Links processed in content stage
    content_saved: Number,          // Content items saved
    links_failed: Number,           // Failed links
    duration: Number,               // Source execution time (seconds)
    error: String | null,           // Error message if failed
    pipeline_mode: Boolean          // Pipeline execution mode flag
  }>,
  
  merger_result: {
    status: String,                 // Merger execution status
    merged_count: Number,           // Total merged threat records
    confidence_stats: {
      low: Number,                  // Low confidence count
      medium: Number,               // Medium confidence count
      high: Number                  // High confidence count
    },
    error: String | null,           // Error message if failed
    timestamp: ISODate              // Merger execution time
  },
  
  created_at: ISODate,              // Task creation time
  updated_at: ISODate               // Last update time
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `task_id_1` | `task_id: 1` | Unique | Ensure unique task IDs |
| `start_time_-1` | `start_time: -1` | Descending | Sort by start time |
| `status_1` | `status: 1` | Standard | Filter by status |
| `task_type_1` | `task_type: 1` | Standard | Filter by type |

### Pipeline Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Crawler   │───▶│    Links    │───▶│   Content   │───▶│   Analysis  │
│  (20 sources)│    │  Discovery  │    │ Extraction  │    │  & Parsing  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
                                                        ┌─────────────┐
                                                        │   Merger    │
                                                        │  (Dedup &   │
                                                        │   Enrich)   │
                                                        └─────────────┘
                                                                │
                                                                ▼
                                                        ┌─────────────┐
                                                        │   Threat    │
                                                        │Intelligence │
                                                        └─────────────┘
```

### Example Query

```javascript
// Get latest 10 completed tasks
db.pipeline_tasks.find({ status: "completed" })
  .sort({ start_time: -1 })
  .limit(10)

// Calculate average execution time for scheduled tasks
db.pipeline_tasks.aggregate([
  { $match: { task_type: "scheduled", status: "completed" } },
  { $group: { _id: null, avg_duration: { $avg: "$total_duration" } } }
])

// Get source performance statistics
db.pipeline_tasks.aggregate([
  { $unwind: "$source_results" },
  { $group: {
      _id: "$source_results.source",
      avg_duration: { $avg: "$source_results.duration" },
      total_links: { $sum: "$source_results.links_discovered" },
      success_rate: { $avg: { $cond: [
        { $eq: ["$source_results.status", "success"] }, 1, 0
      ] } }
  } }
])
```

---

## 5. links Collection

**Purpose:** Stores discovered links from all crawler sources before content extraction.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  timestamp: String,                // Unique timestamp identifier
  source: String,                   // Source platform name
  url: String,                      // Link URL (unique)
  post_date: String,                // Publication date (YYYY-MM-DD)
  collected_at: String,             // Collection timestamp (ISO format)
  status: String,                   // Processing status (pending, processed, failed)
  has_content: Boolean,             // Content extraction completed
  has_analysis: Boolean,            // Analysis completed
  created_at: ISODate,              // Document creation time
  updated_at: ISODate               // Last update time
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `url_1` | `url: 1` | Unique | Prevent duplicate URLs |
| `source_1_discovered_at_-1` | `source: 1, discovered_at: -1` | Compound | Source-specific queries |
| `post_date_-1` | `post_date: -1` | Descending | Sort by publication date |
| `timestamp_1` | `timestamp: 1` | Standard | Query by timestamp |

### Supported Sources (20 Crawlers)

1. **snykdb** - Snyk Vulnerability Database
2. **github** - GitHub Security Advisories
3. **sonatype** - Sonatype Security Research
4. **phylum** - Phylum Package Analysis
5. **thehackernews** - The Hacker News
6. **tuxcare** - TuxCare Security Blog
7. **medium** - Medium Security Articles
8. **checkpoint** - Check Point Research
9. **qianxin** - Qianxin Tianwen
10. **fortinet** - Fortinet FortiGuard Labs
11. **rhisac** - RH-ISAC
12. **checkmarx** - Checkmarx Security
13. **cybersecuritynews** - Cybersecurity News
14. **jfrog** - JFrog Security Research
15. **socketdev** - Socket.dev Security
16. **snyk** - Snyk Blog
17. **bleepingcomputer** - BleepingComputer
18. **reversinglabs** - ReversingLabs
19. **datadoghq** - Datadog Security Labs
20. **securityaffairs** - Security Affairs

### Example Query

```javascript
// Get unprocessed links
db.links.find({ status: "pending" }).limit(100)

// Get links from specific source in date range
db.links.find({
  source: "snyk",
  post_date: { $gte: "2025-01-01", $lte: "2025-12-31" }
}).sort({ post_date: -1 })

// Count links by source
db.links.aggregate([
  { $group: { _id: "$source", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

---

## 6. content Collection

**Purpose:** Stores extracted content from processed links before analysis.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  timestamp: String,                // Unique timestamp identifier (linked to links)
  source: String,                   // Source platform name
  url: String,                      // Original URL
  content: String,                  // Extracted text content
  extracted_at: ISODate             // Content extraction timestamp
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `timestamp_1` | `timestamp: 1` | Unique | Link to links collection |
| `source_1_collected_at_-1` | `source: 1, collected_at: -1` | Compound | Source-specific queries |

### Content Extraction Process

1. **HTML Parsing:** Extract main content from HTML using BeautifulSoup
2. **Text Cleaning:** Remove ads, navigation, boilerplate
3. **Language Detection:** Identify content language
4. **Metadata Extraction:** Extract publish date, author, tags
5. **Storage:** Save cleaned content for analysis

### Example Query

```javascript
// Get content by timestamp
db.content.findOne({ timestamp: "20250928_142053_992327" })

// Search content by keywords
db.content.find({
  content: { $regex: /supply chain attack/i }
}).limit(10)

// Get content statistics by source
db.content.aggregate([
  { $group: {
      _id: "$source",
      count: { $sum: 1 },
      avg_content_length: { $avg: { $strLenCP: "$content" } }
  } }
])
```

---

## 7. analysis Collection

**Purpose:** Stores analysis results from the content processing pipeline.

### Document Structure

```javascript
{
  _id: ObjectId,                    // MongoDB unique identifier
  timestamp: String,                // Unique timestamp identifier (linked to links/content)
  source: String,                   // Source platform name
  url: String,                      // Original URL
  post_date: String,                // Publication date
  step: String,                     // Analysis step (extract, parse, enrich)
  result: Object,                   // Analysis results (structure varies by step)
  created_at: ISODate               // Analysis timestamp
}
```

### Indexes

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `_id_` | `_id: 1` | Default | Primary key |
| `timestamp_1_step_1` | `timestamp: 1, step: 1` | Compound | Query by timestamp and step |
| `source_1_created_at_-1` | `source: 1, created_at: -1` | Compound | Source-specific queries |
| `step_1` | `step: 1` | Standard | Filter by analysis step |

### Analysis Steps

1. **extract:** Extract structured data from content
   - Package names
   - Versions
   - CVE IDs
   - URLs
   - Indicators of Compromise

2. **parse:** Parse and normalize extracted data
   - Normalize package names
   - Parse version ranges
   - Classify attack methods
   - Identify targets

3. **enrich:** Enrich with additional context
   - Cross-reference with other sources
   - Add confidence scores
   - Link to related threats

### Example Query

```javascript
// Get all analysis results for a specific link
db.analysis.find({
  timestamp: "20250928_142053_992327"
}).sort({ step: 1 })

// Get extraction results from last 24 hours
db.analysis.find({
  step: "extract",
  created_at: { $gte: new Date(Date.now() - 24*60*60*1000) }
})

// Count analysis by step
db.analysis.aggregate([
  { $group: { _id: "$step", count: { $sum: 1 } } }
])
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CRAWLER SOURCES (20)                         │
│  snykdb, github, sonatype, phylum, thehackernews, tuxcare, medium,  │
│  checkpoint, qianxin, fortinet, rhisac, checkmarx, jfrog, socket,   │
│  snyk, bleepingcomputer, reversinglabs, datadog, securityaffairs... │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   LINKS COLLECTION    │
                    │  (28,867 documents)   │
                    │   Status: pending     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  CONTENT COLLECTION   │
                    │   (8,755 documents)   │
                    │  Extracted text data  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  ANALYSIS COLLECTION  │
                    │  (217,567 documents)  │
                    │ Extract, Parse, Enrich│
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      MERGER STAGE     │
                    │  Deduplicate & Merge  │
                    └───────────┬───────────┘
                                │
                                ▼
            ┌───────────────────────────────────────┐
            │    THREAT_INTELLIGENCE COLLECTION     │
            │          (40,531 documents)           │
            │      Merged, Deduplicated Data        │
            └───────────────────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────┐
                │       API ENDPOINTS       │
                │  /api/threats (with auth) │
                └───────────────────────────┘
                                │
                                ▼
                ┌───────────────────────────┐
                │     FRONTEND DISPLAY      │
                │  Database Page (200/500)  │
                └───────────────────────────┘
```

---

## Access Control Matrix

| User Type | Homepage | Pipeline Monitor | Database Page | Max Items |
|-----------|----------|------------------|---------------|-----------|
| **Unauthenticated** | ✅ Full | ✅ Full | ✅ Limited | 200 items |
| **Authenticated** | ✅ Full | ✅ Full | ✅ Extended | 500 items (configurable) |
| **Admin** | ✅ Full | ✅ Full | ✅ Unlimited | Unlimited (future) |

---

## Performance Considerations

### Query Optimization Tips

1. **Use Indexes:** Always filter on indexed fields
2. **Projection:** Only fetch required fields
3. **Limit Results:** Use `.limit()` for large datasets
4. **Aggregation:** Use aggregation pipeline for complex queries
5. **Compound Indexes:** Leverage compound indexes for multi-field queries

### Recommended Practices

```javascript
// ✅ Good - Uses index and projection
db.threat_intelligence.find(
  { package_manager: "npm", "metadata.confidence_level": "high" },
  { package_name: 1, package_versions: 1, _id: 0 }
).limit(100)

// ❌ Bad - Full collection scan, fetches all fields
db.threat_intelligence.find({}).toArray()

// ✅ Good - Efficient aggregation with index
db.pipeline_tasks.aggregate([
  { $match: { status: "completed" } },  // Uses index
  { $project: { task_id: 1, total_duration: 1 } },
  { $sort: { start_time: -1 } },
  { $limit: 10 }
])
```

---

## Backup and Maintenance

### Backup Strategy

```bash
# Full database backup
docker exec intelliradar-mongodb mongodump \
  --db intelliradar \
  --out /backup/$(date +%Y%m%d)

# Backup specific collection
docker exec intelliradar-mongodb mongodump \
  --db intelliradar \
  --collection threat_intelligence \
  --out /backup/threats_$(date +%Y%m%d)
```

### Restore

```bash
# Restore full database
docker exec intelliradar-mongodb mongorestore \
  --db intelliradar \
  /backup/20251011

# Restore specific collection
docker exec intelliradar-mongodb mongorestore \
  --db intelliradar \
  --collection threat_intelligence \
  /backup/threats_20251011/intelliradar/threat_intelligence.bson
```

### Maintenance Tasks

```javascript
// Rebuild indexes
db.threat_intelligence.reIndex()

// Compact collection (reduce storage)
db.runCommand({ compact: "threat_intelligence" })

// Check index usage
db.threat_intelligence.aggregate([
  { $indexStats: {} }
])

// Remove old login history (keep last 90 days)
db.login_history.deleteMany({
  login_time: { $lt: new Date(Date.now() - 90*24*60*60*1000) }
})
```

---

## Environment Variables

Configuration options for database access control:

```bash
# Backend environment variables
FREE_USER_MAX_ITEMS=200           # Unauthenticated user limit
DEFAULT_USER_VIEW_LIMIT=500       # Authenticated user default limit
ACCESS_TOKEN_EXPIRE_MINUTES=30    # JWT token expiration time
SECRET_KEY=your-secret-key        # JWT signing key
MONGODB_URL=mongodb://mongodb:27017  # Database connection URL
```

---

## API Endpoints Using Database

### Authentication

- `POST /api/auth/register` - Uses: `users`
- `POST /api/auth/login` - Uses: `users`, `login_history`
- `GET /api/auth/me` - Uses: `users`

### Threat Intelligence

- `GET /api/threats` - Uses: `threat_intelligence`
- `GET /api/threats/:id` - Uses: `threat_intelligence`

### Pipeline Monitoring

- `GET /api/pipeline/stats` - Uses: `pipeline_tasks`
- `GET /api/pipeline/tasks` - Uses: `pipeline_tasks`
- `GET /api/pipeline/sources` - Uses: `pipeline_tasks`

### Statistics

- `GET /api/stats/overview` - Uses: `threat_intelligence`, `pipeline_tasks`
- `GET /api/stats/sources` - Uses: `threat_intelligence`

---

## Contact Information

For business inquiries, enterprise features, or API access:

📧 **Email:** honywenair@163.com

---

## Document Version

- **Version:** 1.0
- **Last Updated:** October 11, 2025
- **Database Version:** MongoDB 7.0
- **Application Version:** ChainGuard v1.0

---

## License

This database structure documentation is proprietary to the ChainGuard project.

