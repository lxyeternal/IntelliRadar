#!/usr/bin/env python3
"""
MongoDB Package Versions 标准化脚本

用于标准化 threat_intelligence 表中的 package_versions 字段，
将各种表示"所有版本"的格式统一为 ["*"]，其他版本信息保持标准化格式。
"""

import os
import sys
from typing import Any, List, Dict
from pymongo import MongoClient
from datetime import datetime
import json

# 添加后端路径到系统路径
backend_path = os.path.join(os.path.dirname(__file__), 'intelliradar_docker', 'backend')
sys.path.append(backend_path)

class PackageVersionsNormalizer:
    """Package Versions 标准化处理器"""
    
    def __init__(self, connection_string: str = None):
        """初始化MongoDB连接"""
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client.intelliradar
        self.threat_intelligence = self.db.threat_intelligence
        
        print(f"✅ 连接到MongoDB数据库: {self.db.name}")
        
        # 统计初始状态
        total_count = self.threat_intelligence.count_documents({})
        print(f"📊 threat_intelligence表总记录数: {total_count}")
    
    def _normalize_package_versions(self, package_versions: Any) -> List[str]:
        """
        标准化包版本信息，将各种表示"所有版本"的格式统一为 ["*"]
        
        Args:
            package_versions: 包版本信息，可能是字符串、列表等
            
        Returns:
            List[str]: 标准化后的版本信息列表，如果处理失败则返回原始数据
        """
        try:
            # 定义表示"所有版本"的模式
            all_version_patterns = {"*", ">= 0", "", "[0,)", ">=0", "> 0", "[0,∞)", "all", "[0,]", "[*]" }
            
            # 如果是None或空，返回 ["*"]
            if not package_versions:
                return ["*"]
            
            # 如果是字符串
            if isinstance(package_versions, str):
                cleaned_version = package_versions.strip()
                if cleaned_version in all_version_patterns:
                    return ["*"]
                return [cleaned_version]
            
            # 如果是列表
            if isinstance(package_versions, list):
                if not package_versions:
                    return ["*"]
                
                # 检查列表中是否有任何一个元素表示"所有版本"
                has_universal_version = False
                normalized_versions = []
                
                for version in package_versions:
                    if isinstance(version, str):
                        cleaned = version.strip()
                        if cleaned in all_version_patterns:
                            has_universal_version = True
                            break  # 只要发现一个全版本标识符就可以跳出
                        else:
                            normalized_versions.append(cleaned)
                    else:
                        normalized_versions.append(str(version))
                
                # 如果有任何一个版本表示"所有版本"，直接返回 ["*"]
                if has_universal_version:
                    return ["*"]
                
                # 去重并排序具体版本
                if not normalized_versions:
                    return ["*"]
                
                unique_versions = list(set(normalized_versions))
                return sorted(unique_versions)
            
            # 其他类型处理：转为字符串处理
            return [str(package_versions)]
            
        except Exception as e:
            # 如果处理过程中出现任何异常，返回原始数据
            print(f"⚠️  版本标准化失败，返回原始数据: {e}")
            
            # 尝试将原始数据转换为合适的格式，避免再次抛出异常
            try:
                if isinstance(package_versions, list):
                    return package_versions
                elif isinstance(package_versions, str):
                    return [package_versions]
                elif package_versions is None:
                    return ["*"]
                else:
                    # 尝试转换为字符串，如果失败则返回默认值
                    try:
                        return [str(package_versions)]
                    except Exception:
                        return ["*"]
            except Exception:
                # 如果连基本的类型检查都失败，返回安全的默认值
                return ["*"]
    
    def normalize_all_records(self, batch_size: int = 1000, dry_run: bool = True) -> Dict[str, int]:
        """
        批量标准化所有记录中的 package_versions 字段
        
        Args:
            batch_size: 每批处理的记录数
            dry_run: 是否为试运行模式（只显示会修改什么，不实际修改）
        
        Returns:
            Dict: 处理统计信息
        """
        stats = {
            'total_processed': 0,
            'modified_count': 0,
            'error_count': 0,
            'skipped_count': 0
        }
        
        print(f"🔄 开始批量处理（批大小: {batch_size}，{'试运行' if dry_run else '实际修改'}）...")
        
        # 使用游标分批处理
        cursor = self.threat_intelligence.find({}, {'_id': 1, 'package_versions': 1, 'package_name': 1})
        
        batch = []
        for doc in cursor:
            batch.append(doc)
            
            if len(batch) >= batch_size:
                batch_stats = self._process_batch(batch, dry_run)
                self._update_stats(stats, batch_stats)
                batch = []
                
                # 显示进度
                if stats['total_processed'] % (batch_size * 5) == 0:
                    print(f"📈 已处理: {stats['total_processed']} 条记录")
        
        # 处理最后一批
        if batch:
            batch_stats = self._process_batch(batch, dry_run)
            self._update_stats(stats, batch_stats)
        
        # 显示最终统计
        print(f"\n📊 处理完成统计:")
        print(f"   总处理记录数: {stats['total_processed']}")
        print(f"   修改记录数: {stats['modified_count']}")
        print(f"   跳过记录数: {stats['skipped_count']}")
        print(f"   错误记录数: {stats['error_count']}")
        
        if dry_run:
            print(f"\n💡 这是试运行结果，如需实际修改，请设置 dry_run=False")
        
        return stats
    
    def _process_batch(self, batch: List[Dict], dry_run: bool) -> Dict[str, int]:
        """处理一批记录"""
        batch_stats = {
            'total_processed': 0,
            'modified_count': 0,
            'error_count': 0,
            'skipped_count': 0
        }
        
        for doc in batch:
            batch_stats['total_processed'] += 1
            
            try:
                original_versions = doc.get('package_versions')
                normalized_versions = self._normalize_package_versions(original_versions)
                
                # 检查是否需要修改
                if original_versions != normalized_versions:
                    if dry_run:
                        # 试运行模式：只显示会修改的内容
                        print(f"📝 [{doc.get('package_name', 'unknown')}] 将修改:")
                        print(f"   原始: {original_versions}")
                        print(f"   标准化: {normalized_versions}")
                        batch_stats['modified_count'] += 1
                    else:
                        # 实际修改
                        result = self.threat_intelligence.update_one(
                            {'_id': doc['_id']},
                            {'$set': {'package_versions': normalized_versions}}
                        )
                        
                        if result.modified_count > 0:
                            batch_stats['modified_count'] += 1
                        else:
                            batch_stats['error_count'] += 1
                else:
                    batch_stats['skipped_count'] += 1
                    
            except Exception as e:
                print(f"❌ 处理记录失败 {doc.get('_id')}: {e}")
                batch_stats['error_count'] += 1
        
        return batch_stats
    
    def _update_stats(self, total_stats: Dict[str, int], batch_stats: Dict[str, int]):
        """更新总统计信息"""
        for key in total_stats:
            total_stats[key] += batch_stats[key]
    
    def sample_analysis(self, sample_size: int = 100) -> Dict:
        """
        分析样本数据，了解当前 package_versions 字段的分布情况
        
        Args:
            sample_size: 样本大小
            
        Returns:
            Dict: 分析结果
        """
        print(f"🔍 正在分析 {sample_size} 条样本数据...")
        
        # 随机采样
        pipeline = [
            {'$sample': {'size': sample_size}},
            {'$project': {'package_versions': 1, 'package_name': 1, '_id': 0}}
        ]
        
        samples = list(self.threat_intelligence.aggregate(pipeline))
        
        # 分析统计
        analysis = {
            'total_samples': len(samples),
            'version_types': {},
            'universal_version_count': 0,
            'list_type_count': 0,
            'string_type_count': 0,
            'empty_or_null_count': 0,
            'examples': {
                'universal_versions': [],
                'specific_versions': [],
                'complex_versions': []
            }
        }
        
        all_version_patterns = {"*", ">= 0", "", "[0,)", ">=0", "> 0", "[0,∞)", "all", "[0,]", "[*]"}
        
        for sample in samples:
            versions = sample.get('package_versions')
            package_name = sample.get('package_name', 'unknown')
            
            # 类型统计
            if versions is None or (isinstance(versions, list) and not versions):
                analysis['empty_or_null_count'] += 1
            elif isinstance(versions, list):
                analysis['list_type_count'] += 1
                
                # 检查是否包含通用版本模式
                has_universal = any(str(v).strip() in all_version_patterns for v in versions)
                if has_universal:
                    analysis['universal_version_count'] += 1
                    if len(analysis['examples']['universal_versions']) < 5:
                        analysis['examples']['universal_versions'].append({
                            'package_name': package_name,
                            'versions': versions
                        })
                else:
                    if len(versions) > 3:  # 复杂版本
                        if len(analysis['examples']['complex_versions']) < 5:
                            analysis['examples']['complex_versions'].append({
                                'package_name': package_name,
                                'versions': versions
                            })
                    else:  # 具体版本
                        if len(analysis['examples']['specific_versions']) < 5:
                            analysis['examples']['specific_versions'].append({
                                'package_name': package_name,
                                'versions': versions
                            })
                            
            elif isinstance(versions, str):
                analysis['string_type_count'] += 1
                if versions.strip() in all_version_patterns:
                    analysis['universal_version_count'] += 1
        
        # 显示分析结果
        print(f"\n📈 样本分析结果:")
        print(f"   样本总数: {analysis['total_samples']}")
        print(f"   列表类型: {analysis['list_type_count']}")
        print(f"   字符串类型: {analysis['string_type_count']}")
        print(f"   空值/空列表: {analysis['empty_or_null_count']}")
        print(f"   包含通用版本模式: {analysis['universal_version_count']}")
        
        print(f"\n🔍 示例数据:")
        if analysis['examples']['universal_versions']:
            print(f"   通用版本示例:")
            for example in analysis['examples']['universal_versions']:
                print(f"     {example['package_name']}: {example['versions']}")
        
        if analysis['examples']['specific_versions']:
            print(f"   具体版本示例:")
            for example in analysis['examples']['specific_versions']:
                print(f"     {example['package_name']}: {example['versions']}")
        
        if analysis['examples']['complex_versions']:
            print(f"   复杂版本示例:")
            for example in analysis['examples']['complex_versions']:
                print(f"     {example['package_name']}: {example['versions']}")
        
        return analysis
    
    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB连接已关闭")


def main():
    """主函数"""
    print("🚀 MongoDB Package Versions 标准化工具")
    print("=" * 50)
    
    # 初始化处理器
    normalizer = PackageVersionsNormalizer()
    
    try:
        # 1. 首先进行样本分析
        print("\n📊 第一步：样本数据分析")
        analysis = normalizer.sample_analysis(sample_size=200)
        
        # 2. 询问用户是否继续
        print(f"\n⚠️  即将处理 threat_intelligence 表中的所有记录")
        
        # 3. 先进行试运行
        print(f"\n🧪 第二步：试运行（前100条记录）")
        dry_run_stats = normalizer.normalize_all_records(batch_size=100, dry_run=True)
        
        # 4. 询问是否进行实际修改
        if dry_run_stats['modified_count'] > 0:
            print(f"\n🔧 发现 {dry_run_stats['modified_count']} 条记录需要修改")
            response = input("是否继续进行实际修改？(y/N): ").lower().strip()
            
            if response == 'y':
                print(f"\n✅ 第三步：开始实际修改")
                actual_stats = normalizer.normalize_all_records(batch_size=1000, dry_run=False)
                print(f"\n🎉 修改完成！实际修改了 {actual_stats['modified_count']} 条记录")
            else:
                print(f"\n❌ 用户取消操作")
        else:
            print(f"\n✅ 所有记录的 package_versions 字段都已经是标准格式，无需修改")
            
    except KeyboardInterrupt:
        print(f"\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
    finally:
        normalizer.close()


if __name__ == "__main__":
    main()
