#!/usr/bin/env python3
"""
测试本地数据库连接和QianXin爬虫数据保存功能
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler.sources.qianxin import QianxinCrawler
from database.mongodb_manager import MongoDBStorageManager


def test_database_connection():
    """测试MongoDB连接"""
    print("🔍 测试MongoDB连接...")
    
    try:
        # 使用本地MongoDB
        storage = MongoDBStorageManager("mongodb://localhost:27017/")
        
        # 测试连接
        collections = storage.db.list_collection_names()
        print(f"✅ 成功连接到数据库: {storage.db.name}")
        print(f"📁 现有集合: {collections}")
        
        return storage
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请确保MongoDB服务正在运行: brew services start mongodb-community")
        return None


def test_qianxin_crawler(storage):
    """测试QianXin爬虫"""
    print("\n🕷️ 测试QianXin爬虫...")
    
    try:
        # 创建爬虫实例并设置MongoDB存储
        crawler = QianxinCrawler()
        crawler.storage = storage  # 使用MongoDB存储
        
        # 设置测试模式：只爬取前2页
        original_config = crawler.config.copy()
        crawler.config["max_pages"] = 2  # 只爬取2页
        
        print("📋 开始爬取...")
        result = crawler.run()
        
        # 恢复原设置
        crawler.config = original_config
        
        return result
    except Exception as e:
        print(f"❌ 爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_saved_data(storage):
    """检查保存的数据"""
    print("\n📊 检查保存的数据...")
    
    try:
        # 检查链接集合
        links_count = storage.links.count_documents({"source": "qianxin"})
        print(f"🔗 QianXin链接数量: {links_count}")
        
        # 检查内容集合
        content_count = storage.content.count_documents({"source": "qianxin"})
        print(f"📄 QianXin内容数量: {content_count}")
        
        # 检查分析集合
        analysis_count = storage.analysis.count_documents({"source": "qianxin"})
        print(f"🔬 QianXin分析数量: {analysis_count}")
        
        # 显示最新的几条记录
        if links_count > 0:
            print("\n📋 最新链接示例:")
            latest_links = storage.links.find(
                {"source": "qianxin"}
            ).sort("discovered_at", -1).limit(3)
            
            for i, link in enumerate(latest_links, 1):
                print(f"  {i}. {link.get('url', 'N/A')}")
                print(f"     标题: {link.get('title', 'N/A')}")
                print(f"     发现时间: {link.get('discovered_at', 'N/A')}")
                print()
        
        return True
    except Exception as e:
        print(f"❌ 数据检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 IntelliRadar 本地数据库测试")
    print("=" * 60)
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 1. 测试数据库连接
    storage = test_database_connection()
    if not storage:
        return
    
    # 2. 测试QianXin爬虫
    result = test_qianxin_crawler(storage)
    if not result:
        return
    
    # 3. 显示爬虫结果
    print(f"\n📈 爬虫运行结果:")
    print(f"   状态: {result.get('status', 'unknown')}")
    print(f"   发现链接: {result.get('links_discovered', 0)}")
    print(f"   保存内容: {result.get('content_saved', 0)}")
    print(f"   失败链接: {result.get('links_failed', 0)}")
    print(f"   运行时间: {result.get('duration', 0):.2f}秒")
    
    # 4. 检查保存的数据
    check_saved_data(storage)
    
    # 5. 关闭连接
    storage.close()
    
    print("\n✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
