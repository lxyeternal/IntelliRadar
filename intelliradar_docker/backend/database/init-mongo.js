// MongoDB Initialization Script for IntelliRadar
// This script runs when MongoDB container starts for the first time

// Switch to the intelliradar database
db = db.getSiblingDB('intelliradar');

// Create application user with read/write permissions
db.createUser({
  user: 'intelliradar_app',
  pwd: 'app_password_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'intelliradar'
    }
  ]
});

// Create collections with validation schemas
db.createCollection('links', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['timestamp', 'source', 'url', 'post_date', 'collected_at'],
      properties: {
        timestamp: { bsonType: 'string' },
        source: { bsonType: 'string' },
        url: { bsonType: 'string' },
        post_date: { bsonType: 'string' },
        collected_at: { bsonType: 'string' },
        status: { bsonType: 'string', enum: ['pending', 'processed', 'failed'] },
        has_content: { bsonType: 'bool' },
        has_analysis: { bsonType: 'bool' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('content', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['timestamp', 'source', 'content'],
      properties: {
        timestamp: { bsonType: 'string' },
        source: { bsonType: 'string' },
        content: { bsonType: 'string' },
        content_type: { bsonType: 'string' },
        file_size: { bsonType: 'int' },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('analysis', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['timestamp', 'source', 'step', 'result'],
      properties: {
        timestamp: { bsonType: 'string' },
        source: { bsonType: 'string' },
        step: { bsonType: 'string', enum: ['extract', 'relation', 'verify', 'error'] },
        step_number: { bsonType: 'int' },
        result: { bsonType: 'object' },
        status: { bsonType: 'string', enum: ['success', 'failed', 'pending'] },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('sources', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['source_name'],
      properties: {
        source_name: { bsonType: 'string' },
        total_links: { bsonType: 'int' },
        with_content: { bsonType: 'int' },
        with_analysis: { bsonType: 'int' },
        status: { bsonType: 'string', enum: ['active', 'inactive', 'error'] },
        last_crawl: { bsonType: 'date' },
        last_update: { bsonType: 'date' }
      }
    }
  }
});

// Create indexes for better performance
db.links.createIndex({ "url": 1 }, { unique: true });
db.links.createIndex({ "source": 1, "collected_at": -1 });
db.links.createIndex({ "post_date": -1 });
db.links.createIndex({ "timestamp": 1 });

db.content.createIndex({ "timestamp": 1 }, { unique: true });
db.content.createIndex({ "source": 1, "created_at": -1 });

db.analysis.createIndex({ "timestamp": 1, "step": 1 });
db.analysis.createIndex({ "source": 1, "created_at": -1 });
db.analysis.createIndex({ "step": 1 });

db.sources.createIndex({ "source_name": 1 }, { unique: true });

// Insert initial source configurations
const initialSources = [
  'github', 'snykdb', 'qianxin', 'datadoghq', 'rhisac', 'checkpoint',
  'phylum', 'securityaffairs', 'fortinet', 'reversinglabs', 'tuxcare',
  'cybersecuritynews', 'socketdev', 'checkmarx', 'snyk', 'sonatype',
  'medium', 'jfrog', 'bleepingcomputer', 'osv', 'aikido'
];

initialSources.forEach(sourceName => {
  db.sources.insertOne({
    source_name: sourceName,
    total_links: 0,
    with_content: 0,
    with_analysis: 0,
    status: 'active',
    last_crawl: null,
    last_update: new Date(),
    crawl_stats: {
      total_crawls: 0,
      successful_crawls: 0,
      avg_links_per_crawl: 0.0,
      last_crawl_duration: 0.0
    }
  });
});

print('✅ IntelliRadar MongoDB initialization completed!');
print('📊 Created collections: links, content, analysis, sources');
print('🔐 Created application user: intelliradar_app');
print('📈 Created indexes for optimal performance');
print(`🎯 Initialized ${initialSources.length} data sources`);
