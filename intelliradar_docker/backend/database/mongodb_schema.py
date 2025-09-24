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
        self.threat_intelligence = self.db.threat_intelligence  # 最终聚合的威胁情报
        
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
        
        # Threat Intelligence collection indexes
        self.threat_intelligence.create_index([("id", ASCENDING)], unique=True)
        self.threat_intelligence.create_index([("package_name", ASCENDING)])
        self.threat_intelligence.create_index([("package_manager", ASCENDING)])
        self.threat_intelligence.create_index([("metadata.last_updated", DESCENDING)])
        self.threat_intelligence.create_index([("metadata.confidence_level", ASCENDING)])
    
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
    
    def get_threat_intelligence_schema(self) -> Dict:
        """Threat Intelligence document schema - 完全按照用户提供的scheme结构"""
        return {
            "_id": "ObjectId",              # MongoDB自动生成的ID
            "id": "str",                    # 唯一标识符，如 "IR-20241223-pypi-a7b3c8d2"
            "package_name": "str",          # 包名，如 "shlackbot"
            "package_manager": "str",       # 包管理器，如 "pypi", "npm", "maven"
            "package_versions": "list",     # 受影响的版本列表，如 ["1.0.0", "1.0.1"]
            "repository_url": "list",        # 仓库URL
            
            "credit": {                     # 来源信息
                "sources": "list",          # 来源列表，从analysis记录聚合: [{discoverer, data_source, discovery_date, source_link}]
                "collected_at": "str"       # 收集时间 (ISO格式)
            },
            
            "references": "list",           # 参考链接列表，每个包含url和type
            
            "threat_info": {                # 威胁信息
                "attack_methods": "list",   # 攻击方法列表
                "attack_vectors": "list",   # 攻击向量列表
                "targets": "list",          # 目标系统列表
            },
            
            "patch_info": "dict",           # 修复信息，包含fix_method等
            
            "indicators_of_compromise": "list",  # IOC指标列表
            
            "metadata": {                   # 元数据
                "created_at": "str",        # 创建时间 (ISO格式)
                "last_updated": "str",      # 最后更新时间 (ISO格式)
                "data_quality_score": "float",  # 数据质量分数 (0-1)
                "confidence_level": "str"   # 置信度级别 ("high", "medium", "low")
            }
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
    THREAT_INTELLIGENCE = "threat_intelligence"


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
