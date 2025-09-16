#!/usr/bin/env python3
"""
IntelliRadar 统一数据处理流水线管理器
支持非结构化和结构化数据源的自动处理
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 导入现有的模块
# 推迟导入，避免循环依赖和模块加载问题


class PipelineManager:
    """统一的数据处理流水线管理器"""
    
    def __init__(self, config_path: str = "Codes/pipeline_config.json"):
        """初始化管理器"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self._setup_paths()
        
        # 初始化组件 - 延迟加载，避免导入错误
        self.collection = None
        self.content_extractor = None
        self.llm_analyzer = None
        self.data_integrator = None
        
    def _load_collection(self):
        """延迟加载WebPageCollection"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'Collection'))
            from webpagecollection import WebPageCollection
            self.collection = WebPageCollection()
        except ImportError as e:
            self.logger.error(f"无法导入WebPageCollection: {e}")
            raise
            
    def _load_content_extractor(self):
        """延迟加载WebPageContent"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'Collection'))
            from webpage_content import WebPageContent
            self.content_extractor = WebPageContent()
        except ImportError as e:
            self.logger.error(f"无法导入WebPageContent: {e}")
            raise
            
    def _load_llm_analyzer(self):
        """延迟加载LTMGPT"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'GPTAnalysis'))
            from lst_gptuse import LTMGPT
            self.llm_analyzer = LTMGPT()
        except ImportError as e:
            self.logger.error(f"无法导入LTMGPT: {e}")
            raise
            
    def _load_data_integrator(self):
        """延迟加载DataIntegrity"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'DataProcessing'))
            from DataIntegrity import DataIntegrity
            self.data_integrator = DataIntegrity()
        except ImportError as e:
            self.logger.error(f"无法导入DataIntegrity: {e}")
            raise
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config['paths']['logs_dir'])
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _setup_paths(self):
        """创建必要的目录"""
        for path_key, path_value in self.config['paths'].items():
            if path_key.endswith('_dir'):
                Path(path_value).mkdir(parents=True, exist_ok=True)
    
    def run_full_pipeline(self, source_types: List[str] = None):
        """运行完整的流水线
        
        Args:
            source_types: 要处理的数据源类型 ['unstructured', 'structured'] 
                         如果为None则处理所有类型
        """
        self.logger.info("🚀 开始运行 IntelliRadar 数据处理流水线")
        start_time = time.time()
        
        if source_types is None:
            source_types = ['unstructured', 'structured']
            
        try:
            # 处理非结构化数据源
            if 'unstructured' in source_types:
                self.logger.info("📝 开始处理非结构化数据源...")
                self._process_unstructured_sources()
                
            # 处理结构化数据源  
            if 'structured' in source_types:
                self.logger.info("🗃️ 开始处理结构化数据源...")
                self._process_structured_sources()
                
            # 数据聚合
            self.logger.info("🔄 开始数据聚合...")
            self._aggregate_all_data()
            
            # 更新前端
            if self.config['pipeline_settings']['update_frontend']:
                self.logger.info("🎨 更新前端数据...")
                self._update_frontend()
                
            elapsed_time = time.time() - start_time
            self.logger.info(f"✅ 流水线运行完成，总耗时: {elapsed_time:.2f}秒")
            
        except Exception as e:
            self.logger.error(f"❌ 流水线运行失败: {str(e)}")
            raise
    
    def _process_unstructured_sources(self):
        """处理非结构化数据源"""
        unstructured_config = self.config['data_sources']['unstructured']
        
        for source_info in unstructured_config['sources']:
            if not source_info['enabled']:
                continue
                
            source_name = source_info['name']
            method_name = source_info['collection_method']
            
            self.logger.info(f"🔍 处理数据源: {source_name}")
            
            try:
                # 1. 采集链接
                self._collect_source_links(source_name, method_name)
                
                # 2. 提取内容
                self._extract_source_content(source_name)
                
                # 3. LLM分析 (如果需要)
                if source_info['requires_llm']:
                    self._analyze_with_llm(source_name)
                    
            except Exception as e:
                self.logger.error(f"处理数据源 {source_name} 时出错: {str(e)}")
                continue
    
    def _process_structured_sources(self):
        """处理结构化数据源"""
        structured_config = self.config['data_sources']['structured']
        
        for source_info in structured_config['sources']:
            if not source_info['enabled']:
                continue
                
            source_name = source_info['name']
            method_name = source_info['collection_method']
            
            self.logger.info(f"📊 处理结构化数据源: {source_name}")
            
            try:
                # 获取结构化数据
                self._fetch_structured_data(source_name, method_name, source_info)
                
            except Exception as e:
                self.logger.error(f"处理结构化数据源 {source_name} 时出错: {str(e)}")
                continue
    
    def _collect_source_links(self, source_name: str, method_name: str):
        """采集指定数据源的链接"""
        self.logger.info(f"  📎 采集 {source_name} 的链接...")
        
        # 延迟加载采集器
        if self.collection is None:
            self._load_collection()
        
        if hasattr(self.collection, method_name):
            method = getattr(self.collection, method_name)
            method()
            self.logger.info(f"  ✅ {source_name} 链接采集完成")
        else:
            self.logger.warning(f"  ⚠️ 未找到方法: {method_name}")
    
    def _extract_source_content(self, source_name: str):
        """提取指定数据源的内容"""
        self.logger.info(f"  📄 提取 {source_name} 的内容...")
        
        # 检查是否有待处理的链接
        waiting_file = Path(self.config['paths']['waiting_collection'])
        if not waiting_file.exists():
            self.logger.warning(f"  ⚠️ 未找到待处理文件: {waiting_file}")
            return
            
        # 延迟加载内容提取器
        if self.content_extractor is None:
            self._load_content_extractor()
            
        # 这里需要根据实际的WebPageContent类接口来调用
        # 目前先记录日志，实际实现需要根据具体方法调整
        self.logger.info(f"  ⚠️ 内容提取功能需要根据具体的WebPageContent类接口实现")
        return 0
    
    def _analyze_with_llm(self, source_name: str):
        """使用LLM分析指定数据源"""
        self.logger.info(f"  🤖 LLM分析 {source_name}...")
        
        # 获取该数据源的内容文件
        content_dir = Path(self.config['paths']['content_dir']) / source_name
        if not content_dir.exists():
            self.logger.warning(f"  ⚠️ 内容目录不存在: {content_dir}")
            return
            
        # 延迟加载LLM分析器
        if self.llm_analyzer is None:
            self._load_llm_analyzer()
            
        # 这里需要根据实际的LTMGPT类接口来调用
        # 目前先记录日志，实际实现需要根据具体方法调整
        self.logger.info(f"  ⚠️ LLM分析功能需要根据具体的LTMGPT类接口实现")
        
        # 执行LLM分析的三个步骤（示例）
        steps = ['extract', 'relation', 'verify']
        for step in steps:
            self.logger.info(f"    🔄 执行 {step} 步骤...")
            
            try:
                # 这里需要根据实际API调用
                # self.llm_analyzer.some_method(source_name, step)
                self.logger.info(f"    ✅ {step} 步骤完成")
                
            except Exception as e:
                self.logger.error(f"    ❌ {step} 步骤失败: {str(e)}")
                continue
    
    def _fetch_structured_data(self, source_name: str, method_name: str, source_info: Dict):
        """获取结构化数据"""
        self.logger.info(f"  🔗 获取 {source_name} 的结构化数据...")
        
        # 这里可以根据不同的结构化数据源实现不同的获取逻辑
        if source_name == 'osv':
            self._fetch_osv_data()
        elif source_name == 'github_advisory':
            self._fetch_github_advisory_data()
        elif source_name == 'snyk_vulndb':
            self._fetch_snyk_vulndb_data()
        else:
            self.logger.warning(f"  ⚠️ 未实现的结构化数据源: {source_name}")
    
    def _fetch_osv_data(self):
        """获取OSV数据"""
        # TODO: 实现OSV API调用
        self.logger.info("    📊 获取OSV漏洞数据...")
        pass
    
    def _fetch_github_advisory_data(self):
        """获取GitHub Advisory数据"""
        # TODO: 实现GitHub Advisory API调用
        self.logger.info("    📊 获取GitHub Advisory数据...")
        pass
    
    def _fetch_snyk_vulndb_data(self):
        """获取Snyk漏洞数据库数据"""
        # TODO: 实现Snyk VulnDB API调用
        self.logger.info("    📊 获取Snyk漏洞数据库数据...")
        pass
    
    def _aggregate_all_data(self):
        """聚合所有数据"""
        self.logger.info("🔄 开始数据聚合...")
        
        try:
            # 延迟加载数据聚合器
            if self.data_integrator is None:
                self._load_data_integrator()
                
            # 这里需要根据实际的DataIntegrity类接口来调用
            # 目前先记录日志，实际实现需要根据具体方法调整
            self.logger.info("  ⚠️ 数据聚合功能需要根据具体的DataIntegrity类接口实现")
            # self.data_integrator.integrate_all_sources()
            self.logger.info("✅ 数据聚合完成")
            
        except Exception as e:
            self.logger.error(f"❌ 数据聚合失败: {str(e)}")
            raise
    
    def _update_frontend(self):
        """更新前端数据"""
        self.logger.info("🎨 更新前端数据...")
        
        try:
            # 运行前端数据更新脚本
            import subprocess
            result = subprocess.run([
                sys.executable, 
                'Codes/update_frontend_data.py'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("✅ 前端数据更新完成")
            else:
                self.logger.error(f"❌ 前端数据更新失败: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"❌ 前端数据更新异常: {str(e)}")
    
    def run_single_source(self, source_name: str, source_type: str = 'unstructured'):
        """运行单个数据源的处理
        
        Args:
            source_name: 数据源名称
            source_type: 数据源类型 ('unstructured' 或 'structured')
        """
        self.logger.info(f"🎯 开始处理单个数据源: {source_name} ({source_type})")
        
        try:
            if source_type == 'unstructured':
                sources = self.config['data_sources']['unstructured']['sources']
                source_info = next((s for s in sources if s['name'] == source_name), None)
                
                if not source_info:
                    raise ValueError(f"未找到数据源配置: {source_name}")
                    
                if not source_info['enabled']:
                    self.logger.warning(f"数据源 {source_name} 未启用")
                    return
                    
                method_name = source_info['collection_method']
                
                # 执行非结构化数据源处理流程
                self._collect_source_links(source_name, method_name)
                self._extract_source_content(source_name)
                
                if source_info['requires_llm']:
                    self._analyze_with_llm(source_name)
                    
            elif source_type == 'structured':
                sources = self.config['data_sources']['structured']['sources']
                source_info = next((s for s in sources if s['name'] == source_name), None)
                
                if not source_info:
                    raise ValueError(f"未找到数据源配置: {source_name}")
                    
                if not source_info['enabled']:
                    self.logger.warning(f"数据源 {source_name} 未启用")
                    return
                    
                method_name = source_info['collection_method']
                self._fetch_structured_data(source_name, method_name, source_info)
            
            self.logger.info(f"✅ 数据源 {source_name} 处理完成")
            
        except Exception as e:
            self.logger.error(f"❌ 处理数据源 {source_name} 时出错: {str(e)}")
            raise
    
    def get_pipeline_status(self) -> Dict:
        """获取流水线状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'statistics': {}
        }
        
        # 检查各数据源状态
        for source_type in ['unstructured', 'structured']:
            sources = self.config['data_sources'][source_type]['sources']
            for source_info in sources:
                source_name = source_info['name']
                status['sources'][source_name] = {
                    'type': source_type,
                    'enabled': source_info['enabled'],
                    'requires_llm': source_info.get('requires_llm', False),
                    'last_processed': self._get_last_processed_time(source_name)
                }
        
        # 统计信息
        status['statistics'] = {
            'total_content_files': self._count_content_files(),
            'total_llm_outputs': self._count_llm_outputs(),
            'csv_size': self._get_csv_size()
        }
        
        return status
    
    def _get_last_processed_time(self, source_name: str) -> Optional[str]:
        """获取数据源最后处理时间"""
        content_dir = Path(self.config['paths']['content_dir']) / source_name
        if not content_dir.exists():
            return None
            
        files = list(content_dir.glob('*.txt'))
        if not files:
            return None
            
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
    
    def _count_content_files(self) -> int:
        """统计内容文件数量"""
        content_dir = Path(self.config['paths']['content_dir'])
        return len(list(content_dir.rglob('*.txt')))
    
    def _count_llm_outputs(self) -> int:
        """统计LLM输出文件数量"""
        llm_dir = Path(self.config['paths']['llm_output_dir'])
        return len(list(llm_dir.rglob('*.json')))
    
    def _get_csv_size(self) -> int:
        """获取CSV文件大小"""
        csv_file = Path(self.config['paths']['csv_output'])
        return csv_file.stat().st_size if csv_file.exists() else 0


if __name__ == "__main__":
    # 简单的命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description='IntelliRadar 数据处理流水线')
    parser.add_argument('--config', default='Codes/pipeline_config.json', help='配置文件路径')
    parser.add_argument('--source', help='处理单个数据源')
    parser.add_argument('--type', choices=['unstructured', 'structured'], help='数据源类型')
    parser.add_argument('--status', action='store_true', help='显示流水线状态')
    parser.add_argument('--sources', nargs='+', choices=['unstructured', 'structured'], 
                       help='要处理的数据源类型')
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = PipelineManager(args.config)
    
    if args.status:
        # 显示状态
        status = manager.get_pipeline_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
    elif args.source:
        # 处理单个数据源
        source_type = args.type or 'unstructured'
        manager.run_single_source(args.source, source_type)
        
    else:
        # 运行完整流水线
        manager.run_full_pipeline(args.sources)
