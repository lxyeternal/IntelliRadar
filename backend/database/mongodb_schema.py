"""
MongoDB Schema Design for IntelliRadar
Replaces file-based storage with MongoDB collections
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from typing import Dict, List, Optional, Any
from datetime import datetime
import os


class MongoDBSchema:
    """MongoDB schema definitions for IntelliRadar"""
    
    def __init__(self, connection_string: str = None):
        """Initialize MongoDB connection"""
        if connection_string is None:
            # Default to environment variable or localhost
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client.intelliradar
        
        # Initialize collections
        self.links = self.db.links              # 替代 all_links.json
        self.content = self.db.content          # 替代 content/*.txt
        self.analysis = self.db.analysis        # 替代 json/*/*.json
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for optimal query performance"""
        
        # Links collection indexes
        self.links.create_index([("url", ASCENDING)], unique=True)  # URL唯一索引
        self.links.create_index([("source", ASCENDING), ("discovered_at", DESCENDING)])
        self.links.create_index([("post_date", DESCENDING)])
        self.links.create_index([("timestamp", ASCENDING)])
        
        # Content collection indexes  
        self.content.create_index([("timestamp", ASCENDING)], unique=True)
        self.content.create_index([("source", ASCENDING), ("collected_at", DESCENDING)])
        
        # Analysis collection indexes
        self.analysis.create_index([("timestamp", ASCENDING), ("step", ASCENDING)])
        self.analysis.create_index([("source", ASCENDING), ("created_at", DESCENDING)])
        self.analysis.create_index([("step", ASCENDING)])
    
    def get_link_schema(self) -> Dict:
        """Link document schema - replaces all_links.json entries"""
        return {
            "_id": "ObjectId",              # MongoDB自动生成
            "timestamp": "str",             # 时间戳ID (20241201_143022_abc123)
            "source": "str",                # 数据源名称 (github, snyk, etc.)
            "url": "str",                   # 链接URL (唯一)
            "post_date": "str",             # 发布日期 (YYYY-MM-DD)
            "discovered_at": "datetime",    # 发现时间
            "status": "str",                # 处理状态: pending, processed, failed
            "has_content": "bool",          # 是否有内容
            "has_analysis": "bool",         # 是否有分析结果
        }
    
    def get_content_schema(self) -> Dict:
        """Content document schema - replaces content/*.txt files"""
        return {
            "_id": "ObjectId",
            "timestamp": "str",             # 关联的时间戳ID
            "source": "str",                # 数据源
            "url": "str",                   # 原始URL
            "content": "str",               # 网页内容 (替代.txt文件)
            "post_date": "str",             # 发布日期 (YYYY-MM-DD)
            "collected_at": "datetime",     # 采集时间
        }
    
    def get_analysis_schema(self) -> Dict:
        """Analysis document schema - replaces json/*/*.json files"""
        return {
            "_id": "ObjectId",
            "timestamp": "str",             # 关联的时间戳ID
            "source": "str",                # 数据源
            "url": "str",                   # 原始URL
            "post_date": "str",             # 发布日期 (YYYY-MM-DD)
            "step": "str",                  # 分析步骤: extract, relation, verify
            "result": "dict",               # 分析结果 (原JSON内容)
            "created_at": "datetime",       # 创建时间
        }
    
    # 删除sources集合，不需要统计功能

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


# Collection名称常量
class Collections:
    LINKS = "links"
    CONTENT = "content" 
    ANALYSIS = "analysis"


# 文档状态常量
class DocumentStatus:
    PENDING = "pending"
    PROCESSED = "processed" 
    FAILED = "failed"
    SUCCESS = "success"


# 分析步骤常量
class AnalysisSteps:
    EXTRACT = "extract"      # 实体提取
    RELATION = "relation"    # 关系分析
    VERIFY = "verify"        # 信息验证


if __name__ == "__main__":
    # 测试连接和schema
    schema = MongoDBSchema()
    print("MongoDB Schema initialized successfully!")
    print(f"Database: {schema.db.name}")
    print(f"Collections: {schema.db.list_collection_names()}")
    schema.close()
