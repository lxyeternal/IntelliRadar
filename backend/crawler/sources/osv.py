import os
import git
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from ..content_extractor import ContentExtractor


class OSVCrawler(ContentExtractor):
    """
    OSV Malicious Packages Crawler
    专门用于从OSV仓库收集恶意包信息，不下载包本身
    """
    
    def __init__(self, source_config: dict, storage_manager=None):
        super().__init__()
        self.source_config = source_config
        self.base_dir = source_config.get("base_dir", "content")
        self.records_dir = source_config.get("records_dir", "data/json")
        self.repo_url = source_config.get("osv_repo_url", "https://github.com/ossf/malicious-packages.git")
        
        # MongoDB storage manager
        self.storage = storage_manager
        
        # 设置路径
        self.content_dir = os.path.join(self.base_dir, "content")
        self.osv_repo_path = os.path.join(self.content_dir, "osv")
        
        # 确保目录存在
        self._ensure_directories()
        
        # 加载已处理的ID（从数据库）
        self.processed_ids = self._load_processed_ids_from_db()
        
    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        Path(self.content_dir).mkdir(parents=True, exist_ok=True)
        
    def _load_processed_ids_from_db(self) -> Set[str]:
        """从数据库加载已经处理过的OSV ID集合"""
        if self.storage:
            return self.storage.get_existing_osv_ids()
        else:
            print("⚠️ 未提供storage_manager，无法加载已处理的ID")
            return set()
    
    def clone_or_pull_repo(self):
        """克隆或更新OSV仓库"""
        try:
            if not os.path.exists(self.osv_repo_path):
                print(f"🔄 正在克隆OSV仓库到: {self.osv_repo_path}")
                git.Repo.clone_from(self.repo_url, self.osv_repo_path)
                print("✅ OSV仓库克隆完成")
            else:
                print("🔄 正在更新OSV仓库")
                repo = git.Repo(self.osv_repo_path)
                repo.remotes.origin.pull()
                print("✅ OSV仓库更新完成")
        except Exception as e:
            print(f"❌ OSV仓库操作失败: {e}")
            raise
    
    def _get_json_files(self, directory: str) -> List[str]:
        """获取目录下所有JSON文件"""
        json_files = []
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith('.json'):
                        json_files.append(os.path.join(root, file))
        return json_files
    
    def _extract_package_info(self, osv_data: dict, package_manager: str) -> Optional[dict]:
        """从OSV数据中提取包信息，生成简化的JSON结构"""
        try:
            # 获取受影响的包信息
            affected_list = osv_data.get("affected", [])
            if not isinstance(affected_list, list) or not affected_list:
                return None
            
            # 提取包名和版本信息
            package_names = []
            package_versions = []
            
            for affected in affected_list:
                if isinstance(affected, dict):
                    package_info = affected.get("package", {})
                    if isinstance(package_info, dict):
                        pkg_name = package_info.get("name")
                        if pkg_name:
                            package_names.append(pkg_name)
                            
                        # 提取版本信息
                        versions = affected.get("versions", [])
                        ranges = affected.get("ranges", [])
                        
                        if versions:
                            package_versions.extend(versions)
                        elif ranges:
                            # 如果有ranges但没有specific versions，标记为"*"
                            for range_info in ranges:
                                events = range_info.get("events", [])
                                for event in events:
                                    if event.get("introduced") == "0":
                                        package_versions.append("*")
                                        break
            
            if not package_names:
                return None
            
            # 构建简化的数据结构
            simplified_data = {
                "id": osv_data.get("id", ""),
                "aliases": osv_data.get("aliases", []),
                "summary": osv_data.get("summary", ""),
                "package_manager": package_manager,
                "package_name": package_names[0] if package_names else "",  # 使用第一个包名
                "package_versions": list(set(package_versions)) if package_versions else ["*"],
                "references": osv_data.get("references", []),
                "credits": osv_data.get("credits", []),
                "published": osv_data.get("published", ""),
                "modified": osv_data.get("modified", "")
            }
            
            return simplified_data
            
        except Exception as e:
            print(f"❌ 提取包信息失败: {e}")
            return None
    
    def process_osv_files(self, package_manager: str) -> int:
        """处理指定包管理器的OSV文件"""
        print(f"🔍 正在处理 {package_manager} 包...")
        
        # 确定路径映射
        path_map = {'npm': 'npm', 'pypi': 'pypi'}
        osv_dir = os.path.join(self.osv_repo_path, "osv", "malicious", path_map[package_manager])
        
        if not os.path.exists(osv_dir):
            print(f"⚠️ 目录不存在: {osv_dir}")
            return 0
        
        json_files = self._get_json_files(osv_dir)
        print(f"📁 找到 {len(json_files)} 个JSON文件")
        
        new_count = 0
        skipped_count = 0
        
        for json_file in json_files:
            try:
                # 从文件名提取ID
                file_name = os.path.basename(json_file)
                expected_id = file_name.replace('.json', '')
                
                # 检查是否已处理（基于数据库中的OSV ID）
                if expected_id in self.processed_ids:
                    skipped_count += 1
                    continue
                
                # 读取并解析JSON文件
                with open(json_file, 'r', encoding='utf-8') as f:
                    osv_data = json.load(f)
                
                # 验证ID是否匹配
                actual_id = osv_data.get("id", "")
                if actual_id != expected_id:
                    print(f"⚠️ ID不匹配: 文件名={expected_id}, 内容ID={actual_id}")
                
                # 如果实际ID也已处理，跳过
                if actual_id and actual_id in self.processed_ids:
                    skipped_count += 1
                    continue
                
                # 提取包信息（生成简化JSON结构）
                package_info = self._extract_package_info(osv_data, package_manager)
                if package_info and self.storage:
                    try:
                        # 保存到数据库
                        self.storage.save_osv_vulnerability_data(package_info)
                        
                        # 添加到已处理列表（内存中）
                        self.processed_ids.add(actual_id or expected_id)
                        new_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ 保存到数据库失败 {package_info.get('package_name', 'unknown')}: {e}")
                
            except Exception as e:
                print(f"❌ 处理文件失败 {json_file}: {e}")
                continue
        
        print(f"✅ {package_manager} 处理完成: 新增={new_count}, 跳过={skipped_count}")
        return new_count
    
    
    def collect_links(self) -> int:
        """收集链接 - OSV爬虫不需要此功能，返回0"""
        return 0
    
    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """提取内容 - OSV爬虫不需要此功能"""
        return None
    
    def run(self) -> dict:
        """运行OSV爬虫主流程"""
        print("🚀 启动OSV恶意包爬虫...")
        
        if not self.storage:
            error_msg = "未提供storage_manager，无法保存数据"
            print(f"❌ {error_msg}")
            return {
                "source": "osv",
                "status": "error",
                "error": error_msg,
                "total_new_packages": 0
            }
        
        start_time = time.time()
        total_new_packages = 0
        
        try:
            # 1. 克隆或更新仓库
            self.clone_or_pull_repo()
            
            # 2. 处理npm包
            print("\n📦 处理npm包...")
            npm_count = self.process_osv_files('npm')
            total_new_packages += npm_count
            
            # 3. 处理pypi包  
            print("\n🐍 处理PyPI包...")
            pypi_count = self.process_osv_files('pypi')
            total_new_packages += pypi_count
            
            elapsed_time = time.time() - start_time
            
            result = {
                "source": "osv",
                "status": "success",
                "total_new_packages": total_new_packages,
                "npm_packages": npm_count,
                "pypi_packages": pypi_count,
                "execution_time": round(elapsed_time, 2),
                "storage_location": "MongoDB Analysis Collection"
            }
            
            print(f"\n✅ OSV爬虫执行完成!")
            print(f"📊 新增包总数: {total_new_packages}")
            print(f"⏱️ 执行时间: {elapsed_time:.2f}秒")
            
            return result
            
        except Exception as e:
            error_msg = f"OSV爬虫执行失败: {e}"
            print(f"❌ {error_msg}")
            return {
                "source": "osv",
                "status": "error",
                "error": error_msg,
                "total_new_packages": 0
            }


def create_osv_crawler(base_dir: str = None, records_dir: str = None, storage_manager=None) -> OSVCrawler:
    """创建OSV爬虫实例"""
    config = {
        "base_dir": base_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data"),
        "records_dir": records_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "json"),
        "osv_repo_url": "https://github.com/ossf/malicious-packages.git"
    }
    return OSVCrawler(config, storage_manager)