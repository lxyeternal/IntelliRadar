#!/usr/bin/env python3
"""
数据迁移脚本：将本地JSON数据迁移到MongoDB
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from database.mongodb_manager import MongoDBStorageManager

class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.logger = logging.getLogger("data_migrator")
        self._setup_logging()
        
        # Initialize MongoDB storage manager
        self.storage_manager = MongoDBStorageManager()
        
        # Data directories
        self.base_dir = Path(__file__).parent / "data"
        self.links_file = self.base_dir / "links" / "all_links.json"
        self.content_dir = self.base_dir / "content"
        self.json_dir = self.base_dir / "json"
        
        # Statistics
        self.stats = {
            'total_links': 0,
            'migrated_links': 0,
            'migrated_content': 0,
            'migrated_analysis': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('migration.log')
            ]
        )
    
    def load_all_links(self) -> Dict[str, List[Dict]]:
        """加载所有链接数据"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load links file: {e}")
            return {}
    
    def get_content_file(self, source: str, timestamp: str) -> Optional[str]:
        """获取内容文件"""
        content_file = self.content_dir / source / f"{timestamp}.txt"
        if content_file.exists():
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to read content file {content_file}: {e}")
        return None
    
    def get_analysis_files(self, source: str, timestamp: str) -> Dict[str, Optional[Any]]:
        """获取分析文件"""
        analysis_data = {
            'extract': None,
            'relation': None, 
            'verify': None
        }
        
        json_source_dir = self.json_dir / source
        if not json_source_dir.exists():
            return analysis_data
        
        for step in ['extract', 'relation', 'verify']:
            json_file = json_source_dir / f"{timestamp}_{step}.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        analysis_data[step] = self.normalize_analysis_data(data, step)
                except Exception as e:
                    self.logger.warning(f"Failed to read {json_file}: {e}")
        
        return analysis_data
    
    def normalize_analysis_data(self, data: Any, step: str) -> Any:
        """标准化分析数据格式"""
        if not data:
            return data
        
        # 处理字段映射
        def normalize_dict(item):
            if isinstance(item, dict):
                normalized = {}
                for key, value in item.items():
                    # 字段映射：Version -> Package Version, Method of Attack -> Attack Method
                    if key == "Version":
                        normalized["Package Version"] = value
                    elif key == "Method of Attack":
                        normalized["Attack Method"] = value
                    else:
                        normalized[key] = normalize_dict(value) if isinstance(value, (dict, list)) else value
                return normalized
            elif isinstance(item, list):
                return [normalize_dict(i) for i in item]
            else:
                return item
        
        return normalize_dict(data)
    
    def process_github_verify_data(self, data: Dict) -> Dict:
        """处理GitHub verify数据格式，确保与MongoDB管理器格式一致"""
        if not isinstance(data, dict):
            return data
        
        result = data.get('result', {})
        if isinstance(result, dict):
            # 标准化GitHub数据格式，匹配MongoDB管理器的期望格式
            normalized_result = {}
            for key, value in result.items():
                if key == "Versions":
                    normalized_result["Package Version"] = value
                elif key == "Description":
                    normalized_result["Attack Method"] = value
                elif key == "GHSA ID":
                    normalized_result["GHSA_ID"] = value
                elif key == "DateTime":
                    # DateTime字段保持原样，会在post_date中使用
                    continue
                else:
                    normalized_result[key] = value
            
            # 直接返回标准化后的结果，不要包装额外的result字段
            # MongoDB管理器会自动将这个作为result字段保存
            return normalized_result
        
        return result
    
    def normalize_field_names(self, data: Dict, source: str) -> Dict:
        """标准化字段名称，确保与MongoDB管理器格式一致"""
        if not isinstance(data, dict):
            return data
        
        # 通用字段映射
        field_mapping = {
            "Version": "Package Version",
            "Method of Attack": "Attack Method",
            "GHSA ID": "GHSA_ID"  # 确保下划线格式
        }
        
        # GitHub特殊映射（已在process_github_verify_data中处理）
        if source == 'github':
            return data
        
        # 应用字段映射
        normalized_data = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            normalized_data[new_key] = value
        
        return normalized_data
    
    def migrate_single_link(self, source: str, link_data: Dict) -> bool:
        """迁移单个链接及其相关数据"""
        try:
            timestamp = link_data.get('timestamp')
            url = link_data.get('url')
            post_date = link_data.get('post_date')
            
            if not all([timestamp, url, post_date]):
                self.logger.warning(f"Missing required fields for {source}: {link_data}")
                self.stats['skipped'] += 1
                return False
            
            # 检查是否已存在
            if self.storage_manager.is_duplicate(url):
                self.logger.debug(f"Link already exists: {timestamp}")
                self.stats['skipped'] += 1
                return False
            
            # 获取内容
            content = self.get_content_file(source, timestamp)
            
            # 获取分析数据
            analysis_data = self.get_analysis_files(source, timestamp)
            
            # 检查可用的数据类型
            has_content = content is not None and content.strip()
            has_analysis = any(analysis_data.values())
            
            # 检查数据完整性
            if source == 'github':
                # GitHub只需要JSON数据，不需要content
                if not has_analysis:
                    self.logger.warning(f"GitHub data missing analysis: {timestamp}")
                    self.stats['skipped'] += 1
                    return False
            else:
                # 其他源需要content和analysis
                if not (has_content or has_analysis):
                    # 如果既没有内容也没有分析，只保存链接元数据
                    self.storage_manager.save_link_entry(
                        source=source,
                        url=url,
                        post_date=post_date,
                        timestamp=timestamp
                    )
                    self.stats['migrated_links'] += 1
                    self.logger.debug(f"Migrated link metadata only: {timestamp}")
                    return True
            
            # 构建分析结果（如果有的话）
            analysis_result = None
            if has_analysis:
                analysis_result = {}
                for step, step_data in analysis_data.items():
                    if step_data is not None:
                        # 特殊处理GitHub verify数据
                        if source == 'github' and step == 'verify':
                            step_data = self.process_github_verify_data(step_data)
                        else:
                            # 对其他数据源应用通用字段标准化
                            if isinstance(step_data, dict) and 'result' in step_data:
                                result = step_data['result']
                                if isinstance(result, (list, dict)):
                                    if isinstance(result, list):
                                        # 处理列表格式的结果
                                        normalized_result = []
                                        for item in result:
                                            if isinstance(item, dict):
                                                normalized_result.append(self.normalize_field_names(item, source))
                                            else:
                                                normalized_result.append(item)
                                        step_data['result'] = normalized_result
                                    else:
                                        # 处理字典格式的结果
                                        step_data['result'] = self.normalize_field_names(result, source)
                        
                        # 添加到分析结果
                        analysis_result[f"{step}_output"] = step_data
                        self.stats['migrated_analysis'] += 1
            
            # 使用统一的保存方法
            self.storage_manager.save_link_with_data(
                source=source,
                url=url,
                post_date=post_date,
                content=content if has_content else "",
                analysis_result=analysis_result,
                timestamp=timestamp  # 传递timestamp
            )
            
            self.stats['migrated_links'] += 1
            if has_content:
                self.stats['migrated_content'] += 1
            
            self.logger.debug(f"Migrated {timestamp}: content={has_content}, analysis={has_analysis}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate {source}/{timestamp}: {e}")
            self.stats['errors'] += 1
            return False
    
    def migrate_source(self, source: str, links: List[Dict]) -> None:
        """迁移单个数据源"""
        self.logger.info(f"Migrating {source}: {len(links)} links")
        
        for i, link_data in enumerate(links, 1):
            if i % 10 == 0:
                self.logger.info(f"Progress {source}: {i}/{len(links)}")
            
            self.migrate_single_link(source, link_data)
    
    def migrate_all(self) -> None:
        """迁移所有数据"""
        self.logger.info("Starting data migration...")
        
        # 加载所有链接数据
        all_links = self.load_all_links()
        if not all_links:
            self.logger.error("No links data found")
            return
        
        # 计算总数
        self.stats['total_links'] = sum(len(links) for links in all_links.values())
        self.logger.info(f"Total links to process: {self.stats['total_links']}")
        
        # 按源迁移
        for source, links in all_links.items():
            self.migrate_source(source, links)
        
        # 迁移Snyk数据库数据
        self.migrate_snyk_db()
        
        # 打印统计信息
        self.print_stats()
    
    def migrate_snyk_db(self) -> None:
        """迁移Snyk数据库数据"""
        snyk_file = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/snyk.json"
        
        if not os.path.exists(snyk_file):
            self.logger.warning(f"Snyk file not found: {snyk_file}")
            return
        
        self.logger.info("Starting Snyk DB migration...")
        
        try:
            with open(snyk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            packages = data.get('packages', [])
            self.logger.info(f"Found {len(packages)} Snyk packages to migrate")
            
            migrated_count = 0
            for i, package in enumerate(packages):
                if i % 100 == 0:
                    self.logger.info(f"Progress Snyk DB: {i}/{len(packages)}")
                
                # 转换为统一格式
                analysis_data = self.convert_snyk_package_to_analysis(package)
                
                # 直接保存到数据库
                try:
                    # 直接插入到MongoDB的analysis集合
                    collection = self.storage_manager.db['analysis']
                    collection.insert_one(analysis_data)
                    migrated_count += 1
                    self.stats['snyk_migrated'] = migrated_count
                except Exception as e:
                    self.logger.error(f"Failed to save Snyk package {package.get('package_name', 'unknown')}: {e}")
                    self.stats['snyk_failed'] = self.stats.get('snyk_failed', 0) + 1
            
            self.logger.info(f"✅ Snyk DB migration completed: {migrated_count} packages migrated")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate Snyk DB: {e}")
    
    def convert_snyk_package_to_analysis(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """将Snyk包数据转换为统一的analysis格式"""
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        return {
            "timestamp": timestamp,
            "source": "snykdb", 
            "url": package.get("data_source_link", ""),
            "post_date": package.get("update_date", ""),
            "step": "verify",
            "result": {
                "Package Name": package.get("package_name"),
                "Package Manager": package.get("package_manager"),
                "Package Version": package.get("affected_version"),
                "Fix Method": package.get("fix_method"),
                "Attack Vector": package.get("overview"),
                "Attack Method": "",  # 空白字段
                "Update Date": package.get("update_date"),
                "References": package.get("reference_links", []),
            },
            "created_at": datetime.utcnow()
        }

    def print_stats(self) -> None:
        """打印迁移统计信息"""
        self.logger.info("Migration completed!")
        self.logger.info("=" * 50)
        self.logger.info(f"Total links processed: {self.stats['total_links']}")
        self.logger.info(f"Links migrated: {self.stats['migrated_links']}")
        self.logger.info(f"Content migrated: {self.stats['migrated_content']}")
        self.logger.info(f"Analysis records migrated: {self.stats['migrated_analysis']}")
        self.logger.info(f"Snyk packages migrated: {self.stats.get('snyk_migrated', 0)}")
        self.logger.info(f"Snyk packages failed: {self.stats.get('snyk_failed', 0)}")
        self.logger.info(f"Skipped: {self.stats['skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info("=" * 50)
        
        # 计算成功率
        if self.stats['total_links'] > 0:
            success_rate = (self.stats['migrated_links'] / self.stats['total_links']) * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")

def main():
    """主函数"""
    migrator = DataMigrator()
    
    # 检查MongoDB连接
    try:
        migrator.storage_manager.get_all_stats()
        print("✓ MongoDB connection successful")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return
    
    # 开始迁移
    migrator.migrate_all()

if __name__ == "__main__":
    main()
