#!/usr/bin/env python3
"""
测试Snyk数据迁移功能
"""
import json
import os
import sys
from datetime import datetime
from migrate_data import DataMigrator

def test_snyk_migration():
    """测试Snyk数据迁移"""
    print("🧪 开始测试Snyk数据迁移...")
    
    # 创建迁移器
    migrator = DataMigrator()
    
    try:
        # 测试连接
        migrator.storage_manager.get_all_stats()
        print("✓ MongoDB连接成功")
    except Exception as e:
        print(f"✗ MongoDB连接失败: {e}")
        return
    
    # 只迁移Snyk数据
    try:
        migrator.migrate_snyk_db()
        print("✅ Snyk数据迁移测试完成")
        
        # 验证数据
        verify_snyk_data(migrator.storage_manager)
        
    except Exception as e:
        print(f"✗ Snyk数据迁移失败: {e}")
        import traceback
        traceback.print_exc()

def verify_snyk_data(storage):
    """验证迁移后的Snyk数据"""
    print("\n🔍 验证迁移后的数据...")
    
    # 查询snykdb数据
    snyk_count = storage.analysis.count_documents({"source": "snykdb"})
    print(f"数据库中的Snyk记录数: {snyk_count}")
    
    if snyk_count > 0:
        # 查看前几条记录的格式
        sample_records = list(storage.analysis.find({"source": "snykdb"}).limit(3))
        
        print("\n📋 样本记录格式:")
        for i, record in enumerate(sample_records, 1):
            print(f"\n--- 记录 {i} ---")
            print(f"Timestamp: {record.get('timestamp')}")
            print(f"Source: {record.get('source')}")
            print(f"URL: {record.get('url')}")
            print(f"Post Date: {record.get('post_date')}")
            print(f"Step: {record.get('step')}")
            
            result = record.get('result', {})
            print(f"Package Name: {result.get('Package Name')}")
            print(f"Package Manager: {result.get('Package Manager')}")
            print(f"Package Version: {result.get('Package Version')}")
            print(f"Attack Vector: {result.get('Attack Vector', '')[:100]}...")  # 只显示前100个字符
            print(f"References: {len(result.get('References', []))} 个链接")

if __name__ == "__main__":
    test_snyk_migration()
