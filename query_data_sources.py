#!/usr/bin/env python3
"""
查询MongoDB中threat_intelligence表的credit.sources.data_source字段的所有唯一值
直接连接本地MongoDB数据库
"""

from pymongo import MongoClient
from collections import Counter
import json

def query_data_sources():
    """查询所有的data_source唯一值"""
    try:
        # 连接本地MongoDB（默认配置）
        client = MongoClient('mongodb://localhost:27017/')
        db = client['intelliradar']  # 数据库名
        collection = db['threat_intelligence']  # 集合名
        
        print("正在连接本地MongoDB数据库...")
        print("数据库: intelliradar")
        print("集合: threat_intelligence")
        print("=" * 60)
        
        # 使用聚合管道查询所有唯一的data_source值
        pipeline = [
            # 展开credit.sources数组
            {"$unwind": "$credit.sources"},
            # 按data_source分组并计数
            {"$group": {
                "_id": "$credit.sources.data_source", 
                "count": {"$sum": 1}
            }},
            # 按计数降序排序
            {"$sort": {"count": -1}}
        ]
        
        print("正在查询所有data_source...")
        
        # 执行聚合查询
        results = list(collection.aggregate(pipeline))
        
        if not results:
            print("没有找到任何data_source数据")
            return
        
        print(f"找到 {len(results)} 个不同的data_source:")
        print()
        
        total_count = 0
        for i, result in enumerate(results, 1):
            data_source = result["_id"]
            count = result["count"]
            total_count += count
            print(f"{i:2d}. {data_source:<30} ({count:,} 条记录)")
        
        print("=" * 60)
        print(f"总计: {total_count:,} 条记录来自 {len(results)} 个不同的数据源")
        
        # 保存结果到JSON文件
        output_data = {
            "total_sources": len(results),
            "total_records": total_count,
            "sources": [
                {
                    "data_source": result["_id"],
                    "count": result["count"]
                } for result in results
            ]
        }
        
        with open('data_sources_report.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n报告已保存到: data_sources_report.json")
        
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        try:
            client.close()
        except:
            pass

def query_data_sources_with_examples():
    """查询data_source并显示每个源的示例记录"""
    try:
        # 连接本地MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['intelliradar']
        collection = db['threat_intelligence']
        
        # 先获取所有唯一的data_source
        pipeline = [
            {"$unwind": "$credit.sources"},
            {"$group": {
                "_id": "$credit.sources.data_source", 
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        data_sources = list(collection.aggregate(pipeline))
        
        print("正在查询每个data_source的详细信息...")
        print("=" * 80)
        
        for ds in data_sources:
            data_source = ds["_id"]
            count = ds["count"]
            
            print(f"\n📊 数据源: {data_source} ({count:,} 条记录)")
            print("-" * 50)
            
            # 查询该数据源的示例记录
            sample_pipeline = [
                {"$unwind": "$credit.sources"},
                {"$match": {"credit.sources.data_source": data_source}},
                {"$limit": 3},
                {"$project": {
                    "package_name": 1,
                    "package_manager": 1,
                    "discoverer": "$credit.sources.discoverer",
                    "discovery_date": "$credit.sources.discovery_date",
                    "source_link": "$credit.sources.source_link"
                }}
            ]
            
            samples = list(collection.aggregate(sample_pipeline))
            
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. 包名: {sample.get('package_name', 'N/A')}")
                print(f"     包管理器: {sample.get('package_manager', 'N/A')}")
                print(f"     发现者: {sample.get('discoverer', 'N/A')}")
                print(f"     发现时间: {sample.get('discovery_date', 'N/A')}")
                source_link = sample.get('source_link', 'N/A')
                if len(str(source_link)) > 80:
                    source_link = str(source_link)[:80] + "..."
                print(f"     来源链接: {source_link}")
                print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        try:
            client.close()
        except:
            pass

def main():
    """主函数"""
    print("IntelliRadar - 数据源查询工具")
    print("连接本地MongoDB数据库 (localhost:27017)")
    print("=" * 60)
    
    while True:
        print("\n请选择查询模式:")
        print("1. 简单查询 - 仅显示data_source列表和计数")
        print("2. 详细查询 - 显示每个data_source的示例记录")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            query_data_sources()
        elif choice == "2":
            query_data_sources_with_examples()
        elif choice == "3":
            print("再见!")
            break
        else:
            print("无效选择，请重新输入。")

if __name__ == "__main__":
    main()
