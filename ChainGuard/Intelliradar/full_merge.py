#!/usr/bin/env python3
"""
IntelliRadar 完整威胁情报合并脚本
将所有verify数据合并并保存到threat_intelligence集合
"""

import os
import sys
import json
from datetime import datetime
from pprint import pprint

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongodb_manager import MongoDBStorageManager
from analysis.intelligence_merger import IntelligenceMerger


def main():
    """主函数：执行完整的威胁情报合并"""
    print("🚀 开始完整威胁情报合并")
    print("=" * 60)
    
    # 1. 初始化数据库管理器
    print("🔧 初始化数据库连接...")
    try:
        db_manager = MongoDBStorageManager()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    # 2. 检查当前状态
    analysis_count = db_manager.analysis.count_documents({"step": "verify"})
    current_threat_count = db_manager.db["threat_intelligence"].count_documents({})
    
    print(f"📊 当前verify数据: {analysis_count} 条")
    print(f"📊 当前威胁情报: {current_threat_count} 条")
    
    if analysis_count == 0:
        print("❌ 没有verify数据可合并")
        return
    
    # 3. 询问用户确认
    if current_threat_count > 0:
        print(f"\n⚠️  数据库中已有 {current_threat_count} 条威胁情报")
        choice = input("是否清空现有数据重新合并？(y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            print("🗑️  清空现有威胁情报数据...")
            result = db_manager.db["threat_intelligence"].delete_many({})
            print(f"✅ 已删除 {result.deleted_count} 条记录")
        else:
            print("⚠️  将在现有数据基础上进行合并")
    
    # 4. 初始化合并器
    print("\n🔧 初始化威胁情报合并器...")
    merger = IntelligenceMerger(db_manager)
    
    # 5. 执行完整合并
    print("\n🚀 开始完整合并...")
    start_time = datetime.now()
    
    try:
        merged_results = merger.merge_intelligence_data()
        
        if not merged_results:
            print("❌ 合并结果为空")
            return
        
        print(f"✅ 合并完成，生成 {len(merged_results)} 个合并结果")
        
        # 6. 统计置信度分布
        confidence_stats = {}
        for result in merged_results:
            level = result['metadata']['confidence_level']
            confidence_stats[level] = confidence_stats.get(level, 0) + 1
        
        print("\n📈 置信度分布:")
        for level, count in confidence_stats.items():
            print(f"  {level.upper()}: {count} 个包")
        
        # 7. 保存所有结果
        print(f"\n💾 开始保存所有 {len(merged_results)} 个结果...")
        save_start_time = datetime.now()
        
        saved_count = merger.save_merged_results(merged_results)
        
        save_end_time = datetime.now()
        save_duration = (save_end_time - save_start_time).total_seconds()
        
        print(f"✅ 成功保存 {saved_count} 个威胁情报")
        print(f"⏱️  保存耗时: {save_duration:.2f} 秒")
        
        # 8. 验证保存结果
        final_count = db_manager.db["threat_intelligence"].count_documents({})
        print(f"📊 最终威胁情报总数: {final_count} 条")
        
        # 9. 显示统计信息
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        print(f"\n" + "=" * 60)
        print("📊 合并统计")
        print("=" * 60)
        print(f"📥 原始verify数据: {analysis_count:,} 条")
        print(f"📤 生成威胁情报: {len(merged_results):,} 个包")
        print(f"💾 成功保存: {saved_count:,} 个包")
        print(f"⏱️  总耗时: {total_duration:.2f} 秒")
        print(f"🚀 处理速度: {len(merged_results)/total_duration:.1f} 包/秒")
        print("=" * 60)
        
        # 10. 显示最新的几条记录
        print("\n📋 最新保存的威胁情报示例:")
        latest_records = db_manager.db["threat_intelligence"].find().sort("metadata.last_updated", -1).limit(10)
        
        for i, record in enumerate(latest_records):
            package_name = record.get('package_name', 'N/A')
            package_manager = record.get('package_manager', 'N/A')
            confidence = record.get('metadata', {}).get('confidence_level', 'N/A')
            versions_count = len(record.get('package_versions', []))
            
            print(f"  {i+1:2d}. {package_name} ({package_manager})")
            print(f"      置信度: {confidence}, 版本数: {versions_count}")
        
        print(f"\n🎉 完整威胁情报合并完成！")
        
    except Exception as e:
        print(f"❌ 合并过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
