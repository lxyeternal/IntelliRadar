#!/usr/bin/env python3
"""
威胁情报聚合功能测试脚本
Test Intelligence Merger functionality
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongodb_manager import MongoDBStorageManager
from analysis.intelligence_merger import IntelligenceMerger


class IntelligenceMergerTester:
    """威胁情报聚合测试器"""
    
    def __init__(self):
        """初始化测试器"""
        print("🚀 初始化威胁情报聚合测试器...")
        
        # 初始化数据库连接
        self.db_manager = MongoDBStorageManager()
        self.db = self.db_manager.db
        
        # 初始化聚合器
        self.merger = IntelligenceMerger(self.db_manager)
        
        # 聚合结果集合名称
        self.merged_collection_name = "threat_intelligence"
        
        print("✅ 测试器初始化完成")
    
    def check_verify_data_status(self):
        """检查verify数据状态"""
        print("\n📊 检查数据库中verify数据状态...")
        
        # 统计verify数据总数
        total_verify = self.db.analysis.count_documents({"step": "verify"})
        print(f"总verify记录数: {total_verify}")
        
        # 统计有效数据（result不为空的）
        valid_verify = self.db.analysis.count_documents({
            "step": "verify", 
            "result": {"$ne": []},
            "result.0": {"$exists": True}
        })
        print(f"有效verify记录数: {valid_verify}")
        
        # 按数据源统计
        pipeline = [
            {"$match": {"step": "verify"}},
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        source_stats = list(self.db.analysis.aggregate(pipeline))
        print(f"按数据源统计:")
        for stat in source_stats:
            print(f"  {stat['_id']}: {stat['count']} 条")
        
        return total_verify, valid_verify
    
    def run_merger_test(self):
        """运行聚合测试"""
        print("\n🔄 开始运行威胁情报聚合测试...")
        
        try:
            # 执行聚合
            merged_results = self.merger.merge_intelligence_data()
            
            if not merged_results:
                print("❌ 聚合结果为空，请检查数据")
                return []
            
            print(f"✅ 聚合完成，生成 {len(merged_results)} 个威胁情报")
            
            # 显示聚合结果统计
            self._display_merge_statistics(merged_results)
            
            return merged_results
            
        except Exception as e:
            print(f"❌ 聚合过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _display_merge_statistics(self, merged_results: List[Dict]):
        """显示聚合结果统计"""
        print(f"\n📈 聚合结果统计:")
        
        # 按包管理器统计
        manager_stats = {}
        confidence_stats = {}
        source_count_stats = {}
        
        for result in merged_results:
            # 包管理器统计
            manager = result.get('package_manager', 'unknown')
            manager_stats[manager] = manager_stats.get(manager, 0) + 1
            
            # 置信度统计
            confidence = result.get('metadata', {}).get('confidence_level', 'unknown')
            confidence_stats[confidence] = confidence_stats.get(confidence, 0) + 1
            
            # 来源数量统计
            source_count = result.get('metadata', {}).get('source_count', 0)
            source_count_stats[source_count] = source_count_stats.get(source_count, 0) + 1
        
        print(f"按包管理器:")
        for manager, count in sorted(manager_stats.items()):
            print(f"  {manager}: {count}")
        
        print(f"按置信度级别:")
        for confidence, count in sorted(confidence_stats.items()):
            print(f"  {confidence}: {count}")
        
        print(f"按来源数量:")
        for source_count, count in sorted(source_count_stats.items()):
            print(f"  {source_count}个来源: {count}个包")
    
    def display_sample_results(self, merged_results: List[Dict], sample_count: int = 3):
        """显示样例结果"""
        print(f"\n📋 显示 {min(sample_count, len(merged_results))} 个聚合结果样例:")
        
        for i, result in enumerate(merged_results[:sample_count]):
            print(f"\n=== 样例 {i+1}: {result.get('package_name')} ===")
            print(f"ID: {result.get('id')}")
            print(f"包管理器: {result.get('package_manager')}")
            print(f"版本: {result.get('version')}")
            print(f"受影响版本: {result.get('package_versions')}")
            print(f"仓库URL: {result.get('repository_url')}")
            
            # 威胁信息
            threat_info = result.get('threat_info', {})
            print(f"攻击方法: {threat_info.get('attack_methods', [])[:2]}...")  # 只显示前2个
            print(f"攻击向量: {threat_info.get('attack_vectors', [])[:2]}...")
            print(f"严重程度: {threat_info.get('severity')}")
            
            # 修复信息
            patch_info = result.get('patch_info', {})
            print(f"修复方法: {patch_info.get('Fix Method', 'N/A')}")
            
            # 元数据
            metadata = result.get('metadata', {})
            print(f"数据质量分数: {metadata.get('data_quality_score')}")
            print(f"置信度级别: {metadata.get('confidence_level')}")
            print(f"来源数量: {metadata.get('source_count')}")
            print(f"高置信度来源: {metadata.get('high_confidence_sources')}")
    
    def save_to_database(self, merged_results: List[Dict]):
        """保存聚合结果到数据库"""
        print(f"\n💾 保存 {len(merged_results)} 个聚合结果到数据库...")
        
        try:
            # 获取或创建威胁情报集合
            collection = self.db[self.merged_collection_name]
            
            # 清空现有数据（可选）
            print(f"清空现有 {self.merged_collection_name} 集合数据...")
            collection.delete_many({})
            
            # 批量插入聚合结果
            if merged_results:
                collection.insert_many(merged_results)
                print(f"✅ 成功保存 {len(merged_results)} 条威胁情报到 {self.merged_collection_name} 集合")
                
                # 创建索引以提高查询性能
                self._create_indexes(collection)
                
                # 验证保存结果
                saved_count = collection.count_documents({})
                print(f"📊 验证: {self.merged_collection_name} 集合现有 {saved_count} 条记录")
            else:
                print("⚠️ 没有数据需要保存")
                
        except Exception as e:
            print(f"❌ 保存数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_indexes(self, collection):
        """为威胁情报集合创建索引"""
        print("📇 创建数据库索引...")
        
        try:
            # 创建常用查询索引
            collection.create_index([("package_name", 1)])
            collection.create_index([("package_manager", 1)])
            collection.create_index([("id", 1)], unique=True)
            collection.create_index([("metadata.last_updated", -1)])
            collection.create_index([("metadata.confidence_level", 1)])
            
            print("✅ 索引创建完成")
            
        except Exception as e:
            print(f"⚠️ 创建索引时出现警告: {e}")
    
    def export_results_to_json(self, merged_results: List[Dict], filename: str = None):
        """导出结果到JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"merged_threat_intelligence_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "output", filename)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(merged_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 聚合结果已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 导出文件时出错: {e}")
            return None
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("🎯 开始完整威胁情报聚合测试流程")
        print("=" * 60)
        
        # 1. 检查数据状态
        total_verify, valid_verify = self.check_verify_data_status()
        
        if valid_verify == 0:
            print("❌ 没有有效的verify数据，无法进行聚合测试")
            return
        
        # 2. 运行聚合
        merged_results = self.run_merger_test()
        
        if not merged_results:
            print("❌ 聚合失败，测试终止")
            return
        
        # 3. 显示样例结果
        self.display_sample_results(merged_results)
        
        # 4. 保存到数据库
        self.save_to_database(merged_results)
        
        # 5. 导出到文件
        self.export_results_to_json(merged_results)
        
        print("\n" + "=" * 60)
        print("🎉 威胁情报聚合测试完成！")
        print(f"✅ 总共处理了 {valid_verify} 条verify数据")
        print(f"✅ 生成了 {len(merged_results)} 个聚合威胁情报")
        print(f"✅ 数据已保存到 {self.merged_collection_name} 集合")


def main():
    """主函数"""
    try:
        tester = IntelligenceMergerTester()
        tester.run_full_test()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
