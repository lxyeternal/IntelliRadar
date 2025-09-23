#!/usr/bin/env python3
"""
IntelliRadar Intelligence Merger 测试脚本
用于测试威胁情报合并功能
"""

import json
from database.mongodb_manager import MongoDBManager
from analysis.intelligence_merger import IntelligenceMerger


def test_merger():
    """测试合并器功能"""
    print("🧪 开始测试威胁情报合并器...")
    
    try:
        # 初始化
        db_manager = MongoDBManager()
        merger = IntelligenceMerger(db_manager)
        
        # 执行合并
        print("\n1️⃣ 执行数据合并...")
        merged_results = merger.merge_intelligence_data()
        
        if not merged_results:
            print("⚠️ 没有找到需要合并的数据")
            return
        
        # 显示合并结果样例
        print(f"\n2️⃣ 合并完成，共生成 {len(merged_results)} 个合并后的威胁情报")
        
        if merged_results:
            print("\n📄 第一个合并结果示例:")
            sample = merged_results[0]
            print(json.dumps(sample, indent=2, ensure_ascii=False))
            
            # 验证schema合规性
            print("\n🔍 Schema验证:")
            required_fields = [
                "id", "package_name", "package_manager", "package_versions",
                "repository_url", "credit", "references", "threat_info", 
                "patch_info", "indicators_of_compromise", "metadata"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in sample:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必需字段: {missing_fields}")
            else:
                print("✅ 所有必需字段都存在")
            
            # 检查package_name是否为string
            if isinstance(sample.get('package_name'), str):
                print("✅ package_name是string类型")
            else:
                print(f"❌ package_name类型错误: {type(sample.get('package_name'))}")
            
            # 检查ID格式
            sample_id = sample.get('id', '')
            if sample_id.startswith('IR-') and len(sample_id.split('-')) >= 4:
                print(f"✅ ID格式正确: {sample_id}")
            else:
                print(f"❌ ID格式错误: {sample_id}")
        
        # 保存结果
        print("\n3️⃣ 保存合并结果到数据库...")
        saved_count = merger.save_merged_results(merged_results)
        
        # 统计信息
        print(f"\n4️⃣ 统计信息:")
        confidence_stats = {}
        source_stats = {}
        
        for result in merged_results:
            # 置信度统计
            level = result['metadata']['confidence_level']
            confidence_stats[level] = confidence_stats.get(level, 0) + 1
            
            # 数据源统计
            source_count = result['metadata']['source_count']
            source_stats[source_count] = source_stats.get(source_count, 0) + 1
        
        print("\n📊 置信度分布:")
        for level in ['high', 'medium', 'low']:
            count = confidence_stats.get(level, 0)
            percentage = (count / len(merged_results)) * 100 if merged_results else 0
            print(f"   {level.upper()}: {count} ({percentage:.1f}%)")
        
        print("\n📊 数据源数量分布:")
        for source_count in sorted(source_stats.keys()):
            count = source_stats[source_count]
            percentage = (count / len(merged_results)) * 100 if merged_results else 0
            print(f"   {source_count} sources: {count} packages ({percentage:.1f}%)")
        
        print(f"\n✅ 测试完成！成功保存 {saved_count} 条合并结果")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


def show_sample_data():
    """显示数据库中的原始数据样例"""
    print("📋 显示数据库中的原始数据样例...")
    
    try:
        db_manager = MongoDBManager()
        
        # 获取verify步骤的数据样例
        sample_data = list(db_manager.analysis.find({"step": "verify"}).limit(3))
        
        if sample_data:
            print(f"\n找到 {len(sample_data)} 条样例数据:")
            for i, data in enumerate(sample_data, 1):
                print(f"\n--- 样例 {i} ---")
                print(f"Source: {data.get('source')}")
                print(f"URL: {data.get('url')}")
                print(f"Post Date: {data.get('post_date')}")
                
                result = data.get('result', {})
                package_name = result.get('Package Name')
                package_manager = result.get('Package Manager')
                
                print(f"Package: {package_name} ({package_manager})")
                
                if isinstance(package_name, list):
                    print(f"  注意：Package Name是列表，包含 {len(package_name)} 个包")
        else:
            print("⚠️ 数据库中没有找到verify步骤的数据")
            
    except Exception as e:
        print(f"❌ 获取样例数据时出错: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("IntelliRadar Intelligence Merger 测试")
    print("=" * 60)
    
    # 先显示样例数据
    show_sample_data()
    
    print("\n" + "=" * 60)
    
    # 运行测试
    test_merger()
    
    print("\n" + "=" * 60)
