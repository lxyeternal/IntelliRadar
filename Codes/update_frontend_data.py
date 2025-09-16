#!/usr/bin/env python3
"""
统一的前端数据更新脚本
将处理后的威胁情报数据转换为前端可用格式
"""

import json
import logging
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class FrontendDataUpdater:
    """前端数据更新器"""
    
    def __init__(self, config_path: str = "Codes/pipeline_config.json"):
        """初始化更新器"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # 路径配置
        self.csv_file = Path(self.config['paths']['csv_output'])
        self.frontend_dir = Path(self.config['paths']['frontend_dir'])
        
        # 输出文件路径
        self.packages_json = self.frontend_dir / "aggregated_packages.json"
        self.stats_json = self.frontend_dir / "Intelliradar_data.json"
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            return {
                'paths': {
                    'csv_output': 'Dataset/CSV/integrity.csv',
                    'frontend_dir': 'frontend/'
                }
            }
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
    
    def update_all_frontend_data(self):
        """更新所有前端数据"""
        self.logger.info("🎨 开始更新前端数据...")
        
        try:
            # 检查CSV文件是否存在
            if not self.csv_file.exists():
                self.logger.error(f"❌ CSV文件不存在: {self.csv_file}")
                return False
            
            # 读取CSV数据
            self.logger.info("📊 读取CSV数据...")
            df = pd.read_csv(self.csv_file)
            self.logger.info(f"✅ 成功读取 {len(df)} 条记录")
            
            # 确保前端目录存在
            self.frontend_dir.mkdir(exist_ok=True)
            
            # 更新包详情数据
            self.logger.info("📦 生成包详情数据...")
            self._update_packages_data(df)
            
            # 更新统计数据
            self.logger.info("📈 生成统计数据...")
            self._update_statistics_data(df)
            
            self.logger.info("✅ 前端数据更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 前端数据更新失败: {str(e)}")
            return False
    
    def _update_packages_data(self, df: pd.DataFrame):
        """更新包详情数据"""
        packages_data = []
        
        for _, row in df.iterrows():
            try:
                # 清理和标准化数据
                package_info = {
                    "packageName": self._clean_string(row.get('Package Name', '')),
                    "packageManager": self._clean_string(row.get('Package Manager', '')),
                    "version": self._parse_version(row.get('Version', '')),
                    "discoveryDate": self._parse_date(row.get('Discovery Date', '')),
                    "repositoryUrl": self._clean_string(row.get('Repository URL', '')),
                    "attackMethod": self._clean_string(row.get('Attack Method', '')),
                    "discoverer": self._clean_string(row.get('Discoverer', '')),
                    "impactedSystems": self._clean_string(row.get('Impacted Systems', '')),
                    "attackVector": self._clean_string(row.get('Attack Vector', '')),
                    "indicatorsOfCompromise": self._clean_string(row.get('Indicators of Compromise', '')),
                    "timestamp": self._parse_date(row.get('Timestamp', '')),
                    "source": self._clean_string(row.get('Source', ''))
                }
                
                # 只添加有效的包信息
                if package_info["packageName"]:
                    packages_data.append(package_info)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 处理记录时出错: {str(e)}")
                continue
        
        # 写入JSON文件
        with open(self.packages_json, 'w', encoding='utf-8') as f:
            json.dump(packages_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ 生成包详情数据: {len(packages_data)} 个包")
    
    def _update_statistics_data(self, df: pd.DataFrame):
        """更新统计数据"""
        try:
            # 基本统计
            total_packages = len(df)
            total_sources = df['Source'].nunique() if 'Source' in df.columns else 0
            
            # 按包管理器统计
            package_manager_stats = {}
            if 'Package Manager' in df.columns:
                pm_counts = df['Package Manager'].value_counts()
                package_manager_stats = pm_counts.to_dict()
            
            # 按数据源统计
            source_stats = {}
            if 'Source' in df.columns:
                source_counts = df['Source'].value_counts()
                source_stats = source_counts.to_dict()
            
            # 按发现时间统计（最近30天）
            recent_discoveries = 0
            if 'Discovery Date' in df.columns:
                df_copy = df.copy()
                df_copy['Discovery Date'] = pd.to_datetime(df_copy['Discovery Date'], errors='coerce')
                recent_date = pd.Timestamp.now() - pd.Timedelta(days=30)
                recent_discoveries = len(df_copy[df_copy['Discovery Date'] > recent_date])
            
            # 构建统计数据
            stats_data = {
                "lastUpdated": datetime.now().isoformat(),
                "totalPackages": total_packages,
                "totalSources": total_sources,
                "recentDiscoveries": recent_discoveries,
                "packageManagerStats": package_manager_stats,
                "sourceStats": source_stats,
                "topPackageManagers": self._get_top_items(package_manager_stats, 5),
                "topSources": self._get_top_items(source_stats, 5),
                "metadata": {
                    "dataVersion": "1.0",
                    "generatedBy": "IntelliRadar Pipeline",
                    "description": "威胁情报统计数据"
                }
            }
            
            # 写入JSON文件
            with open(self.stats_json, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ 生成统计数据: {total_packages} 个包, {total_sources} 个数据源")
            
        except Exception as e:
            self.logger.error(f"❌ 生成统计数据失败: {str(e)}")
    
    def _clean_string(self, value: Any) -> str:
        """清理字符串数据"""
        if pd.isna(value):
            return ""
        
        # 转换为字符串
        str_value = str(value)
        
        # 处理列表格式的字符串 (如 "['item1', 'item2']")
        if str_value.startswith('[') and str_value.endswith(']'):
            try:
                # 尝试解析为Python列表
                import ast
                parsed_list = ast.literal_eval(str_value)
                if isinstance(parsed_list, list):
                    return ", ".join(str(item) for item in parsed_list)
            except:
                pass
        
        return str_value.strip()
    
    def _parse_version(self, value: Any) -> str:
        """解析版本信息"""
        cleaned = self._clean_string(value)
        
        # 如果是列表格式，提取第一个版本
        if cleaned.startswith('[') and cleaned.endswith(']'):
            try:
                import ast
                parsed_list = ast.literal_eval(cleaned)
                if isinstance(parsed_list, list) and parsed_list:
                    return str(parsed_list[0])
            except:
                pass
        
        return cleaned
    
    def _parse_date(self, value: Any) -> str:
        """解析日期"""
        if pd.isna(value):
            return ""
        
        try:
            # 尝试解析日期并标准化格式
            parsed_date = pd.to_datetime(value)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            # 如果解析失败，返回原始字符串
            return str(value).strip()
    
    def _get_top_items(self, stats_dict: Dict, top_n: int) -> List[Dict]:
        """获取前N个统计项"""
        if not stats_dict:
            return []
        
        sorted_items = sorted(stats_dict.items(), key=lambda x: x[1], reverse=True)
        return [
            {"name": name, "count": count} 
            for name, count in sorted_items[:top_n]
        ]
    
    def get_update_status(self) -> Dict:
        """获取更新状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "csv_file": {
                "exists": self.csv_file.exists(),
                "size": self.csv_file.stat().st_size if self.csv_file.exists() else 0,
                "modified": datetime.fromtimestamp(self.csv_file.stat().st_mtime).isoformat() if self.csv_file.exists() else None
            },
            "packages_json": {
                "exists": self.packages_json.exists(),
                "size": self.packages_json.stat().st_size if self.packages_json.exists() else 0,
                "modified": datetime.fromtimestamp(self.packages_json.stat().st_mtime).isoformat() if self.packages_json.exists() else None
            },
            "stats_json": {
                "exists": self.stats_json.exists(),
                "size": self.stats_json.stat().st_size if self.stats_json.exists() else 0,
                "modified": datetime.fromtimestamp(self.stats_json.stat().st_mtime).isoformat() if self.stats_json.exists() else None
            }
        }
        
        return status


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='更新前端数据')
    parser.add_argument('--config', default='Codes/pipeline_config.json', help='配置文件路径')
    parser.add_argument('--status', action='store_true', help='显示更新状态')
    
    args = parser.parse_args()
    
    # 创建更新器
    updater = FrontendDataUpdater(args.config)
    
    if args.status:
        # 显示状态
        status = updater.get_update_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        # 执行更新
        success = updater.update_all_frontend_data()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

