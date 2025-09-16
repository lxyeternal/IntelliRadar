#!/usr/bin/env python3
"""
IntelliRadar 主运行脚本
统一的入口点，用于运行整个数据处理流水线
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加Codes目录到Python路径
sys.path.append('Codes')

from pipeline_manager import PipelineManager


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                     🚀 IntelliRadar 🚀                      ║
    ║                威胁情报自动化收集与分析系统                    ║
    ║                                                              ║
    ║  📊 多源数据采集  🤖 AI智能分析  🔄 自动化处理  📈 可视化展示   ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印使用帮助"""
    help_text = """
🔧 使用方法:

1. 运行完整流水线:
   python run_pipeline.py

2. 只处理非结构化数据源:
   python run_pipeline.py --sources unstructured

3. 只处理结构化数据源:
   python run_pipeline.py --sources structured

4. 处理单个数据源:
   python run_pipeline.py --source snyk --type unstructured

5. 查看系统状态:
   python run_pipeline.py --status

6. 只更新前端数据:
   python run_pipeline.py --frontend-only

7. 列出所有可用的数据源:
   python run_pipeline.py --list-sources

📊 数据源类型:
   - 非结构化: snyk, github_blog, threatpost, darkreading, securityweek 等
   - 结构化: osv, github_advisory, snyk_vulndb

🎯 常用组合:
   - 快速测试: python run_pipeline.py --source snyk --type unstructured
   - 数据更新: python run_pipeline.py --sources unstructured structured
   - 前端刷新: python run_pipeline.py --frontend-only
    """
    print(help_text)


def list_available_sources(config_path: str):
    """列出所有可用的数据源"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件未找到: {config_path}")
        return
    
    print("\n📊 可用的数据源:")
    print("=" * 60)
    
    # 非结构化数据源
    print("\n🔍 非结构化数据源 (需要LLM分析):")
    unstructured = config['data_sources']['unstructured']['sources']
    for i, source in enumerate(unstructured, 1):
        status = "✅ 启用" if source['enabled'] else "❌ 禁用"
        print(f"  {i:2d}. {source['name']:<20} - {status}")
    
    # 结构化数据源
    print("\n📋 结构化数据源 (直接处理):")
    structured = config['data_sources']['structured']['sources']
    for i, source in enumerate(structured, 1):
        status = "✅ 启用" if source['enabled'] else "❌ 禁用"
        api_endpoint = source.get('api_endpoint', 'N/A')
        print(f"  {i:2d}. {source['name']:<20} - {status} ({api_endpoint})")


def show_status(manager: PipelineManager):
    """显示系统状态"""
    print("\n📊 IntelliRadar 系统状态:")
    print("=" * 60)
    
    try:
        status = manager.get_pipeline_status()
        
        # 基本信息
        print(f"🕐 更新时间: {status['timestamp']}")
        print(f"📁 内容文件: {status['statistics']['total_content_files']} 个")
        print(f"🤖 LLM输出: {status['statistics']['total_llm_outputs']} 个")
        print(f"📊 CSV大小: {status['statistics']['csv_size']} 字节")
        
        # 数据源状态
        print("\n📋 数据源状态:")
        for source_name, source_info in status['sources'].items():
            status_icon = "✅" if source_info['enabled'] else "❌"
            type_icon = "🔍" if source_info['type'] == 'unstructured' else "📋"
            llm_icon = "🤖" if source_info.get('requires_llm', False) else "📄"
            last_processed = source_info.get('last_processed', 'Never')
            if last_processed != 'Never':
                last_processed = last_processed[:19]  # 只显示日期和时间
            
            print(f"  {status_icon} {type_icon} {llm_icon} {source_name:<20} - 最后处理: {last_processed}")
        
        print("\n📖 图例:")
        print("  ✅/❌ - 启用/禁用    🔍 - 非结构化    📋 - 结构化    🤖 - 需要LLM    📄 - 直接处理")
        
    except Exception as e:
        print(f"❌ 获取状态失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='IntelliRadar 威胁情报处理系统', add_help=False)
    
    # 基本选项
    parser.add_argument('--config', default='Codes/pipeline_config.json', help='配置文件路径')
    parser.add_argument('--help', '-h', action='store_true', help='显示帮助信息')
    
    # 运行模式
    parser.add_argument('--sources', nargs='+', choices=['unstructured', 'structured'], 
                       help='要处理的数据源类型')
    parser.add_argument('--source', help='处理单个数据源')
    parser.add_argument('--type', choices=['unstructured', 'structured'], help='单个数据源的类型')
    
    # 信息选项
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--list-sources', action='store_true', help='列出所有可用数据源')
    parser.add_argument('--frontend-only', action='store_true', help='只更新前端数据')
    
    # 输出选项
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默运行')
    
    args = parser.parse_args()
    
    # 显示横幅（除非是静默模式）
    if not args.quiet:
        print_banner()
    
    # 显示帮助
    if args.help:
        print_help()
        parser.print_help()
        return 0
    
    # 列出数据源
    if args.list_sources:
        list_available_sources(args.config)
        return 0
    
    # 检查配置文件
    if not Path(args.config).exists():
        print(f"❌ 配置文件不存在: {args.config}")
        print("💡 请先创建配置文件或检查路径是否正确")
        return 1
    
    try:
        # 创建管理器
        manager = PipelineManager(args.config)
        
        # 显示状态
        if args.status:
            show_status(manager)
            return 0
        
        # 只更新前端
        if args.frontend_only:
            print("🎨 只更新前端数据...")
            manager._update_frontend()
            print("✅ 前端数据更新完成")
            return 0
        
        # 处理单个数据源
        if args.source:
            source_type = args.type or 'unstructured'
            print(f"🎯 处理单个数据源: {args.source} ({source_type})")
            start_time = time.time()
            
            manager.run_single_source(args.source, source_type)
            
            elapsed_time = time.time() - start_time
            print(f"✅ 数据源处理完成，耗时: {elapsed_time:.2f}秒")
            return 0
        
        # 运行完整或部分流水线
        sources_to_process = args.sources
        if sources_to_process:
            print(f"🔄 运行部分流水线，处理: {', '.join(sources_to_process)}")
        else:
            print("🚀 运行完整流水线")
            sources_to_process = None
        
        start_time = time.time()
        manager.run_full_pipeline(sources_to_process)
        elapsed_time = time.time() - start_time
        
        print(f"\n🎉 流水线运行完成！")
        print(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
        print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示简要状态
        if not args.quiet:
            print("\n📊 最新状态:")
            show_status(manager)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断了程序运行")
        return 130
        
    except Exception as e:
        print(f"\n❌ 运行失败: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

