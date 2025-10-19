"""
Main entry point for IntelliRadar crawler and intelligence merger
"""

import argparse
import time
import schedule
import threading
from datetime import datetime
from crawler.pipeline import CrawlerPipeline
from analysis.intelligence_merger import IntelligenceMerger
from analysis.source_code_collector import SourceCodeCollector
from database.mongodb_manager import MongoDBStorageManager
from database.task_logger import TaskLogger  # 任务日志记录


def run_crawler(args, task_logger=None, task_id=None):
    """运行爬虫"""
    # Create and run pipeline
    pipeline = CrawlerPipeline(task_id=task_id)
    
    if args.sources:
        # Run specific sources
        results = pipeline.run_sources(args.sources, args.workers)
    else:
        # Run all sources
        results = pipeline.run_all(args.workers)
    
    # 记录爬虫结果到任务日志（不影响原有逻辑）
    if task_logger and task_id:
        task_logger.update_crawler_results(task_id, results)
    
    # Print summary
    print("\n" + "="*50)
    print("CRAWLER SUMMARY")
    print("="*50)
    
    for result in results:
        status_icon = "✓" if result.get('status') == 'success' else "✗"
        source = result.get('source', 'unknown')
        
        if result.get('status') == 'success':
            links = result.get('links_found', 0)
            duration = result.get('duration', 0)
            print(f"{status_icon} {source:<15} {links:>3} links ({duration:.1f}s)")
        else:
            error = result.get('error', 'unknown error')
            print(f"{status_icon} {source:<15} Error: {error}")
    
    print("="*50)
    
    # 如果启用了自动合并，则运行合并
    if args.auto_merge:
        print("\n🔄 开始自动合并威胁情报...")
        run_merger(task_logger=task_logger, task_id=task_id)
    
    return results


def run_merger(task_logger=None, task_id=None):
    """运行威胁情报合并"""
    try:
        # 初始化数据库管理器和合并器
        db_manager = MongoDBStorageManager()
        merger = IntelligenceMerger(db_manager)
        
        # 执行合并
        merged_results = merger.merge_intelligence_data()
        
        # 保存合并结果
        saved_count = merger.save_merged_results(merged_results)
        
        # 打印置信度统计信息
        print("\n" + "="*60)
        print("📈 置信度分布统计")
        print("="*60)
        
        confidence_stats = {}
        for result in merged_results:
            level = result['metadata']['confidence_level']
            confidence_stats[level] = confidence_stats.get(level, 0) + 1
        
        for level, count in confidence_stats.items():
            print(f"📊 {level.upper()} 置信度: {count} 个包")
        
        print("="*60)
        print(f"🎉 威胁情报聚合流程完成！")
        
        # 记录合并结果到任务日志（不影响原有逻辑）
        if task_logger and task_id:
            task_logger.update_merger_result(task_id, saved_count, confidence_stats)
        
    except Exception as e:
        print(f"❌ 合并过程中出错: {e}")
        # 记录错误到任务日志
        if task_logger and task_id:
            task_logger.update_merger_result(task_id, 0, {}, error=str(e))
        raise


def run_collector(show_status=True, auto_confirm=False, task_logger=None, task_id=None):
    """运行源代码收集器"""
    collector = None
    
    try:
        collector = SourceCodeCollector(task_logger=task_logger, task_id=task_id)
        
        if show_status:
            print("\n📊 当前收集状态:")
            status = collector.get_collection_status()
            
            if status:
                print(f"  总包数: {status['total_packages']}")
                print(f"  PyPI: {status['pypi']['collected']}/{status['pypi']['total']} 已收集, "
                      f"{status['pypi']['pending']} 待处理")
                print(f"  npm:  {status['npm']['collected']}/{status['npm']['total']} 已收集, "
                      f"{status['npm']['pending']} 待处理")
        
        if not auto_confirm:
            input("\n⚠️  按 Enter 开始收集，或 Ctrl+C 取消...")
        
        print("\n🚀 开始源代码收集...")
        result = collector.collect_all()
        
        print("\n🎉 源代码收集完成！")
        return result
        
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已被用户取消")
        return None
    except Exception as e:
        print(f"\n❌ 收集过程中出错: {e}")
        import traceback
        traceback.print_exc()
        # 记录错误到任务日志
        if task_logger and task_id:
            task_logger.update_collector_result(task_id, {}, error=str(e))
        raise
    finally:
        if collector:
            collector.close()


def run_scheduled_task():
    """定时任务：运行完整的采集和分析流程"""
    print(f"\n🕷️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始定时采集任务")
    print("="*60)
    
    # 创建任务日志记录器
    task_logger = TaskLogger()
    task_id = None
    
    try:
        # 创建任务记录
        task_id = task_logger.create_task(
            task_type="scheduled",
            trigger_source="cron",
            sources=None,
            workers=3
        )
        
        # 创建 args 对象模拟命令行参数
        class Args:
            def __init__(self):
                self.sources = None  # 采集所有源
                self.workers = 3     # 使用3个工作线程
                self.auto_merge = False
        
        args = Args()
        
        # 步骤1: 运行爬虫
        print("\n📍 步骤 1/3: 运行爬虫采集")
        print("="*60)
        run_crawler(args, task_logger=task_logger, task_id=task_id)
        
        # 步骤2: 运行合并
        print("\n📍 步骤 2/3: 运行情报合并")
        print("="*60)
        run_merger(task_logger=task_logger, task_id=task_id)
        
        # 步骤3: 运行源代码收集
        print("\n📍 步骤 3/3: 运行源代码收集")
        print("="*60)
        run_collector(
            show_status=True, 
            auto_confirm=True,  # 定时任务自动确认，不等待用户输入
            task_logger=task_logger, 
            task_id=task_id
        )
        
        # 标记任务完成
        task_logger.complete_task(task_id, status="completed")
        print("\n" + "="*60)
        print(f"✅ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 定时采集任务完成")
        print(f"   - 爬虫采集: ✓")
        print(f"   - 情报合并: ✓")
        print(f"   - 源码收集: ✓")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 定时采集任务失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 标记任务失败
        if task_id:
            task_logger.fail_task(task_id, str(e))
    finally:
        task_logger.close()


def start_scheduler():
    """启动定时调度器"""
    print("🕐 启动定时调度器...")
    print("⏰ 采集频率: 每12小时执行一次")
    print("🔄 首次执行: 启动后立即执行")
    print("="*50)
    
    # 设置定时任务 - 每12小时执行一次
    schedule.every(12).hours.do(run_scheduled_task)
    
    # 立即执行一次
    print("🚀 立即执行首次采集任务...")
    run_scheduled_task()
    
    # 持续运行调度器
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='IntelliRadar Threat Intelligence Crawler and Merger')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 爬虫命令
    crawler_parser = subparsers.add_parser('crawl', help='Run threat intelligence crawler')
    crawler_parser.add_argument(
        '--sources', 
        nargs='+', 
        help='Specific sources to crawl. Available: qianxin, datadoghq, rhisac, checkpoint, phylum, securityaffairs',
        default=None
    )
    crawler_parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of concurrent workers (default: 3)'
    )
    crawler_parser.add_argument(
        '--auto-merge',
        action='store_true',
        help='Automatically run intelligence merger after crawling'
    )
    
    # 合并命令
    merge_parser = subparsers.add_parser('merge', help='Run intelligence merger only')
    
    # 完整流程命令
    full_parser = subparsers.add_parser('full', help='Run complete pipeline (crawl + merge + collect)')
    full_parser.add_argument(
        '--sources', 
        nargs='+', 
        help='Specific sources to crawl',
        default=None
    )
    full_parser.add_argument(
        '--workers',
        type=int,
        default=3,
        help='Number of concurrent workers (default: 3)'
    )
    
    # 定时任务命令
    scheduler_parser = subparsers.add_parser('schedule', help='Run scheduled tasks (crawl + merge + collect, every 12 hours)')
    
    # 源代码收集命令
    collect_parser = subparsers.add_parser('collect', help='Collect source code for PyPI and npm packages')
    collect_parser.add_argument(
        '--auto-confirm',
        action='store_true',
        help='Skip confirmation prompt and start immediately'
    )
    collect_parser.add_argument(
        '--no-status',
        action='store_true',
        help='Skip showing collection status before starting'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定命令，默认运行爬虫
    if not args.command:
        args.command = 'crawl'
        args.sources = None
        args.workers = 3
        args.auto_merge = False
    
    # 执行对应命令
    if args.command == 'crawl':
        # 创建任务日志（手动爬虫）
        task_logger = TaskLogger()
        try:
            task_id = task_logger.create_task(
                task_type="manual",
                trigger_source="cli",
                sources=args.sources,
                workers=args.workers
            )
            run_crawler(args, task_logger=task_logger, task_id=task_id)
            task_logger.complete_task(task_id, status="completed")
        except Exception as e:
            if task_id:
                task_logger.fail_task(task_id, str(e))
            raise
        finally:
            task_logger.close()
            
    elif args.command == 'merge':
        run_merger()
        
    elif args.command == 'full':
        # 创建任务日志（完整流程）
        task_logger = TaskLogger()
        task_id = None
        try:
            task_id = task_logger.create_task(
                task_type="full",
                trigger_source="cli",
                sources=args.sources,
                workers=args.workers
            )
            # 步骤1: 运行爬虫
            print("\n📍 步骤 1/3: 运行爬虫采集")
            print("="*60)
            args.auto_merge = False  # 避免重复合并
            run_crawler(args, task_logger=task_logger, task_id=task_id)
            
            # 步骤2: 运行合并
            print("\n📍 步骤 2/3: 运行情报合并")
            print("="*60)
            run_merger(task_logger=task_logger, task_id=task_id)
            
            # 步骤3: 运行源代码收集
            print("\n📍 步骤 3/3: 运行源代码收集")
            print("="*60)
            run_collector(
                show_status=True,
                auto_confirm=True,  # 完整流程自动确认
                task_logger=task_logger,
                task_id=task_id
            )
            
            task_logger.complete_task(task_id, status="completed")
        except Exception as e:
            if task_id:
                task_logger.fail_task(task_id, str(e))
            raise
        finally:
            task_logger.close()
        
    elif args.command == 'collect':
        # 运行源代码收集（带任务日志）
        task_logger = TaskLogger()
        task_id = None
        try:
            task_id = task_logger.create_task(
                task_type="source_collection",
                trigger_source="cli",
                sources=None,
                workers=1
            )
            show_status = not args.no_status
            run_collector(
                show_status=show_status, 
                auto_confirm=args.auto_confirm,
                task_logger=task_logger,
                task_id=task_id
            )
            task_logger.complete_task(task_id, status="completed")
        except Exception as e:
            if task_id:
                task_logger.fail_task(task_id, str(e))
            raise
        finally:
            task_logger.close()

    elif args.command == 'schedule':
        # 启动定时调度器
        start_scheduler()
        return


if __name__ == '__main__':
    main()