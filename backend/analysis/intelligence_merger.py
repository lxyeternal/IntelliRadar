"""
IntelliRadar Intelligence Merger
智能威胁情报合并系统

负责将从不同数据源采集到的相同包名和版本的威胁情报进行智能合并
支持数据拆分、置信度评分、字段合并等功能
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import hashlib


class IntelligenceMerger:
    """威胁情报智能合并器"""
    
    def __init__(self, mongodb_manager):
        self.db = mongodb_manager
        
        # 高可信度数据源 (置信度100%)
        self.high_confidence_sources = {'github', 'snykdb', 'osv'}
        
        # 字段映射关系
        self.field_mappings = {
            'attack_methods': ['Attack Method', 'behavior'],
            'attack_vectors': ['Attack Vector', 'overview'],
            'targets': ['Impacted Systems'],
            'discoverer': ['Discoverer'],
            'discovery_date': ['Date of Discovery', 'post_date'],
            'references': ['References'],
            'package_versions': ['Package Version'],
            'version': ['Package Version', 'affected_versions', 'version'],  # 版本字段映射
            'fix_method': ['Fix Method'],
            'credit': ['Credit', 'Discoverer', 'credit']  # 信用字段映射
        }
        
    def merge_intelligence_data(self) -> List[Dict]:
        """
        主合并函数：从数据库获取verify步骤的数据并进行合并
        """
        print("🔄 开始威胁情报合并...")
        
        # 1. 从数据库获取所有verify步骤的数据
        raw_data = self._fetch_verify_data()
        print(f"📊 获取到 {len(raw_data)} 条原始数据")
        
        # 2. 数据拆分和规范化
        normalized_data = self._split_and_normalize_data(raw_data)
        print(f"📊 拆分后得到 {len(normalized_data)} 条标准化数据")
        
        # 3. 按包名和管理器分组
        grouped_data = self._group_by_package(normalized_data)
        print(f"📊 分组后得到 {len(grouped_data)} 个包")
        
        # 4. 对每个包进行合并
        merged_results = []
        for package_key, package_data in grouped_data.items():
            merged_package = self._merge_single_package(package_key, package_data)
            merged_results.append(merged_package)
        
        print(f"✅ 合并完成，生成 {len(merged_results)} 个合并后的威胁情报")
        
        # 5. 标准化包版本信息
        print("🔧 开始标准化包版本信息...")
        normalized_count = 0
        for package in merged_results:
            original_versions = package.get('package_versions', [])
            normalized_versions = self._normalize_package_versions(original_versions)
            if normalized_versions != original_versions:
                package['package_versions'] = normalized_versions
                normalized_count += 1
        
        if normalized_count > 0:
            print(f"✅ 已标准化 {normalized_count} 个包的版本信息")
        else:
            print("ℹ️  所有包的版本信息已是标准格式")
        
        # 6. 对所有合并结果进行列表字段去重
        print("🧹 开始对列表字段进行去重...")
        deduplication_count = 0
        for i, package in enumerate(merged_results):
            original_package = package.copy()
            deduplicated_package = self._deduplicate_data(package)
            
            # 检查是否有变化
            if deduplicated_package != original_package:
                merged_results[i] = deduplicated_package
                deduplication_count += 1
        
        if deduplication_count > 0:
            print(f"✅ 已对 {deduplication_count} 个包的列表字段进行去重")
        else:
            print("ℹ️  所有列表字段已无重复项")
        
        return merged_results
    
    def _deduplicate_data(self, data: Dict) -> Dict:
        """
        通用的数据去重函数，最多处理两层嵌套
        遍历所有key，如果值是list就去重，如果值是dict就递归处理一层
        
        Args:
            data: 需要去重的数据字典
            
        Returns:
            Dict: 去重后的数据字典
        """
        if not isinstance(data, dict):
            return data
        
        result = data.copy()
        
        for key, value in result.items():
            if isinstance(value, list):
                # 如果是列表，直接去重
                result[key] = self._deduplicate_list(value, f"{key}")
            elif isinstance(value, dict):
                # 如果是字典，递归处理一层（第二层）
                nested_dict = value.copy()
                for nested_key, nested_value in nested_dict.items():
                    if isinstance(nested_value, list):
                        nested_dict[nested_key] = self._deduplicate_list(nested_value, f"{key}.{nested_key}")
                result[key] = nested_dict
        
        return result
    
    def _deduplicate_list(self, items: list, field_path: str) -> list:
        """去重列表"""
        if not isinstance(items, list):
            return items
        
        try:
            # 直接用set去重，简单粗暴
            return list(set(items))
        except:
            # 如果有字典等不可哈希类型，就返回原值
            return items
    
    def _fetch_verify_data(self) -> List[Dict]:
        """从数据库获取所有step为verify的数据"""
        try:
            cursor = self.db.analysis.find({"step": "verify"})
            return list(cursor)
        except Exception as e:
            print(f"❌ 获取数据时出错: {e}")
            return []
    
    def _split_and_normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        数据拆分和规范化
        处理result可能是dict（单个结果）或list（多个结果）的情况
        如果Package Name是列表，则拆分为多条记录
        """
        normalized = []
        
        for item in raw_data:
            result = item.get('result', [])
            
            # result可能是dict（单个结果）或list（多个结果）
            if isinstance(result, dict):
                result_list = [result]
            elif isinstance(result, list):
                result_list = result
            else:
                continue
            
            # 处理每个结果项
            for result_item in result_list:
                if not isinstance(result_item, dict):
                    continue
                    
                package_names = result_item.get('Package Name', [])
                
                # 确保package_names是列表
                if isinstance(package_names, str):
                    package_names = [package_names]
                elif not package_names:  # 空值处理
                    continue
                    
                # 为每个包名创建一条记录
                for package_name in package_names:
                    normalized_item = {
                        'source': item.get('source'),
                        'url': item.get('url'),
                        'post_date': item.get('post_date'),
                        'timestamp': item.get('timestamp'),
                        'created_at': item.get('created_at'),
                        'package_name': package_name.strip(),
                        'original_result': result_item
                    }
                    normalized.append(normalized_item)
        
        return normalized
    
    def _group_by_package(self, normalized_data: List[Dict]) -> Dict[str, List[Dict]]:
        """按包名和包管理器分组"""
        grouped = defaultdict(list)
        
        for item in normalized_data:
            result = item['original_result']
            package_name = item['package_name']
            package_manager = result.get('Package Manager', 'unknown')
            
            # 创建唯一键
            key = f"{package_manager}::{package_name}"
            grouped[key].append(item)
        
        return dict(grouped)
    
    def _merge_single_package(self, package_key: str, package_data: List[Dict]) -> Dict:
        """合并单个包的所有数据 - 完全按照用户scheme结构"""
        package_manager, package_name = package_key.split('::', 1)
        
        # 获取最新的post_date
        latest_post_date = self._get_latest_post_date(package_data)
        
        # 生成唯一ID
        package_id = self._generate_package_id(package_name, package_manager, latest_post_date)
        
        # 计算置信度分数
        confidence_info = self._calculate_confidence(package_data)
        
        # 构建credit信息 - 从analysis记录聚合
        credit_sources = []
        for item in package_data:
            result = item['original_result']
            # 从result中提取discoverer信息
            discoverer = result.get('Discoverer', item['source'])
            
            source_info = {
                "discoverer": discoverer,
                "data_source": item['source'],
                "discovery_date": self._normalize_date(item['post_date']),
                "source_link": item['url']
            }
            credit_sources.append(source_info)
        
        # 合并引用链接 - 从result中的references字段
        references = self._merge_references(package_data)
        
        # 合并各个字段，完全按照scheme结构
        merged_result = {
            "id": package_id,
            "package_name": package_name,
            "package_manager": package_manager,
            "package_versions": self._merge_versions(package_data) or [],
            "repository_url": self._extract_repository_urls_as_list(package_data) or [],  # 改为list
            
            "credit": {
                "sources": credit_sources,
                "collected_at": datetime.utcnow().isoformat() + "Z"
            },
            
            "references": references,
            
            "threat_info": {
                "attack_methods": self._merge_field_values(package_data, 'attack_methods') or [],
                "attack_vectors": self._merge_field_values(package_data, 'attack_vectors') or [],
                "targets": self._merge_field_values(package_data, 'targets') or []
            },
            
            "patch_info": {
                "fix_method": self._merge_fix_method_with_default(package_data)
            },
            
            "indicators_of_compromise": self._merge_ioc(package_data) or [],
            
            "metadata": {
                "created_at": "",  # 将在save_merged_results中设置
                "last_updated": "",  # 将在save_merged_results中设置
                "data_quality_score": confidence_info['quality_score'],
                "confidence_level": confidence_info['level']
            }
        }
        
        return merged_result
    
    def _get_latest_post_date(self, package_data: List[Dict]) -> str:
        """获取最新的post_date"""
        latest_date = None
        latest_timestamp = 0
        
        for item in package_data:
            post_date = item.get('post_date')
            if post_date:
                try:
                    # 尝试解析时间戳
                    if isinstance(post_date, str):
                        if 'T' in post_date:
                            dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(post_date, '%Y-%m-%d')
                    else:
                        continue
                    
                    timestamp = dt.timestamp()
                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_date = post_date
                except:
                    continue
        
        return latest_date or datetime.now().strftime("%Y-%m-%d")
    
    def _generate_package_id(self, package_name: str, package_manager: str, post_date: str) -> str:
        """生成包的唯一ID: IR-{post_date}-{package_manager}-{package_name_hash[:8]}"""
        # 从post_date提取日期部分 (YYYY-MM-DD -> YYYYMMDD)
        if post_date:
            try:
                if 'T' in post_date:
                    date_part = post_date.split('T')[0]  # 提取日期部分
                else:
                    date_part = post_date.split(' ')[0]  # 处理其他格式
                date_formatted = date_part.replace('-', '')  # YYYY-MM-DD -> YYYYMMDD
            except:
                date_formatted = datetime.now().strftime("%Y%m%d")
        else:
            date_formatted = datetime.now().strftime("%Y%m%d")
        
        # 使用包名生成hash
        package_hash = hashlib.md5(package_name.encode()).hexdigest()[:8]
        return f"IR-{date_formatted}-{package_manager}-{package_hash}"
    
    def _calculate_confidence(self, package_data: List[Dict]) -> Dict:
        """计算置信度信息"""
        total_sources = len(package_data)
        high_confidence_count = sum(1 for item in package_data 
                                  if item['source'] in self.high_confidence_sources)
        
        # 基础分数：高可信度源占比 * 0.7 + 总源数量因子 * 0.3
        base_score = (high_confidence_count / total_sources) * 0.7
        source_factor = min(total_sources / 5, 1.0) * 0.3  # 最多5个源达到满分
        
        quality_score = base_score + source_factor
        
        # 确定置信度等级
        if quality_score >= 0.8:
            level = "high"
        elif quality_score >= 0.6:
            level = "medium"
        else:
            level = "low"
        
        return {
            'quality_score': round(quality_score, 2),
            'level': level,
            'high_confidence_count': high_confidence_count,
            'total_count': total_sources
        }
    
    def _normalize_package_versions(self, package_versions: Any) -> str:
        """
        标准化包版本信息，将各种表示"所有版本"的格式统一为 "*"
        
        Args:
            package_versions: 包版本信息，可能是字符串、列表等
            
        Returns:
            str: 标准化后的版本信息
        """
        # 定义表示"所有版本"的模式
        all_version_patterns = {"*", ">= 0", "", "[0,)", ">=0", "> 0", "[0,∞)", "all"}
        
        # 如果是None或空，返回 "*"
        if not package_versions:
            return "*"
        
        # 如果是字符串
        if isinstance(package_versions, str):
            cleaned_version = package_versions.strip()
            if cleaned_version in all_version_patterns:
                return "*"
            return cleaned_version
        
        # 如果是列表
        if isinstance(package_versions, list):
            if not package_versions:
                return "*"
            
            # 检查列表中的所有元素是否都表示"所有版本"
            normalized_versions = []
            all_are_universal = True
            
            for version in package_versions:
                if isinstance(version, str):
                    cleaned = version.strip()
                    if cleaned in all_version_patterns:
                        normalized_versions.append("*")
                    else:
                        normalized_versions.append(cleaned)
                        all_are_universal = False
                else:
                    normalized_versions.append(str(version))
                    all_are_universal = False
            
            # 如果所有版本都表示"所有版本"，返回单个 "*"
            if all_are_universal:
                return "*"
            
            # 去重并排序
            unique_versions = list(set(normalized_versions))
            if len(unique_versions) == 1 and unique_versions[0] == "*":
                return "*"
            
            if not unique_versions:
                return "*"
            return unique_versions if len(unique_versions) > 1 else unique_versions[0]
        
        # 其他类型转为字符串处理
        return str(package_versions)
    
    def _merge_versions(self, package_data: List[Dict]) -> List[str]:
        """合并包版本信息"""
        all_versions = set()
        
        for item in package_data:
            versions = item['original_result'].get('Package Version', [])
            if isinstance(versions, str) and versions:
                all_versions.add(versions.strip())
            elif isinstance(versions, list):
                for version in versions:
                    if version and isinstance(version, str):
                        all_versions.add(version.strip())
        
        # 过滤掉空值和None，然后排序
        filtered_versions = [v for v in all_versions if v and v.strip()]
        return sorted(filtered_versions)
    
    def _extract_repository_url(self, package_data: List[Dict]) -> str:
        """提取仓库URL - 保留原方法兼容性"""
        for item in package_data:
            result = item['original_result']
            repo_url = result.get('Repository URL') or result.get('URL')
            if repo_url:
                return repo_url if isinstance(repo_url, str) else repo_url[0]
        return ""
    
    def _extract_repository_urls_as_list(self, package_data: List[Dict]) -> List[str]:
        """提取所有仓库URL作为列表"""
        repository_urls = set()
        
        for item in package_data:
            result = item['original_result']
            repo_url = result.get('Repository URL') or result.get('URL')
            if repo_url:
                if isinstance(repo_url, list):
                    repository_urls.update(repo_url)
                elif isinstance(repo_url, str) and repo_url != "":
                    repository_urls.add(repo_url)
        
        return list(repository_urls)
    
    def _build_credit_info(self, package_data: List[Dict]) -> Dict:
        """构建数据源信息"""
        sources = []
        
        for item in package_data:
            result = item['original_result']
            
            # 提取发现者信息
            discoverer = self._extract_discoverer(result)
            
            source_info = {
                "discoverer": discoverer,
                "data_source": item['source'],
                "discovery_date": self._normalize_date(item['post_date']),
                "source_link": item['url']
            }
            sources.append(source_info)
        
        return {
            "sources": sources,
            "collected_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def _extract_discoverer(self, result: Dict) -> str:
        """提取发现者信息"""
        discoverer = result.get('Discoverer', result.get('Credits', ''))
        
        if isinstance(discoverer, list):
            return ', '.join(discoverer)
        elif isinstance(discoverer, str):
            return discoverer
        else:
            return "Unknown"
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式为ISO格式"""
        if not date_str:
            return ""
        
        try:
            # 尝试解析不同格式的日期
            if '/' in date_str:  # MM/DD/YYYY format
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00Z"
            elif '-' in date_str and 'T' not in date_str:  # YYYY-MM-DD format
                return f"{date_str}T00:00:00Z"
            elif 'T' in date_str:  # Already ISO format
                return date_str if date_str.endswith('Z') else f"{date_str}Z"
        except:
            pass
        
        return date_str
    
    def _merge_references(self, package_data: List[Dict]) -> List[Dict]:
        """合并引用链接"""
        references = []
        seen_urls = set()
        
        for item in package_data:
            result = item['original_result']
            source = item['source']
            
            # 添加源链接
            if item['url'] and item['url'] not in seen_urls:
                references.append({
                    "url": item['url'],
                    "type": source
                })
                seen_urls.add(item['url'])
            
            # 添加result中的References
            refs = result.get('References', [])
            if isinstance(refs, list):
                for ref in refs:
                    if ref and ref not in seen_urls:
                        references.append({
                            "url": ref,
                            "type": "reference"
                        })
                        seen_urls.add(ref)
        
        return references
    
    def _merge_field_values(self, package_data: List[Dict], field_type: str, single_value: bool = False) -> Any:
        """合并字段值 - 只合并非空值"""
        all_values = set()
        field_names = self.field_mappings.get(field_type, [])
        
        for item in package_data:
            result = item['original_result']
            for field_name in field_names:
                value = result.get(field_name)
                # 只处理非空值
                if value and value != "" and value != []:
                    if isinstance(value, list):
                        # 过滤空字符串
                        non_empty_values = [v for v in value if v and v != ""]
                        all_values.update(non_empty_values)
                    else:
                        all_values.add(value)
        
        values_list = list(all_values)
        
        if single_value:
            return values_list[0] if values_list else ""
        else:
            return values_list
    
    def _merge_ioc(self, package_data: List[Dict]) -> List[str]:
        """合并威胁指标"""
        all_iocs = set()
        
        for item in package_data:
            result = item['original_result']
            iocs = result.get('Indicators of Compromise', [])
            
            if isinstance(iocs, list):
                for ioc in iocs:
                    if isinstance(ioc, str):
                        all_iocs.add(ioc.strip())
                    elif isinstance(ioc, dict):
                        # 如果是字典，转换为字符串表示
                        all_iocs.add(str(ioc))
            elif isinstance(iocs, str):
                all_iocs.add(iocs.strip())
            elif isinstance(iocs, dict):
                # 如果是字典，转换为字符串表示
                all_iocs.add(str(iocs))
        
        return list(all_iocs)
    
    def _merge_all_sources_info(self, package_data: List[Dict], field_names: List[str]) -> List[str]:
        """合并所有来源的信息字段（如 references, credit）"""
        all_values = set()
        
        for item in package_data:
            result = item['original_result']
            
            # 添加来源信息
            source = item.get('source', '')
            if source:
                all_values.add(f"Source: {source}")
            
            # 合并指定字段的所有值
            for field_name in field_names:
                value = result.get(field_name)
                if value and value != "" and value != []:
                    if isinstance(value, list):
                        non_empty_values = [v for v in value if v and v != ""]
                        all_values.update(non_empty_values)
                    else:
                        all_values.add(value)
        
        return list(all_values)
    
    def _merge_version_with_priority(self, package_data: List[Dict]) -> str:
        """按优先级合并版本字段：OSV > GitHub > SnykDB > 其他投票选择"""
        # 定义来源优先级
        source_priority = {
            'osv': 1,
            'github': 2, 
            'snykdb': 3
        }
        
        version_candidates = []
        
        for item in package_data:
            result = item['original_result']
            source = item.get('source', '').lower()
            
            # 获取版本字段
            version_fields = self.field_mappings.get('version', [])
            for field_name in version_fields:
                version = result.get(field_name)
                if version and version != "":
                    priority = source_priority.get(source, 999)  # 其他来源优先级最低
                    version_candidates.append({
                        'version': version,
                        'priority': priority,
                        'source': source
                    })
        
        if not version_candidates:
            return ""
        
        # 按优先级排序
        version_candidates.sort(key=lambda x: x['priority'])
        
        # 如果有高优先级来源（OSV、GitHub、SnykDB），直接使用
        if version_candidates[0]['priority'] <= 3:
            return version_candidates[0]['version']
        
        # 其他来源使用投票选择（选择最常见的版本）
        version_counts = {}
        for candidate in version_candidates:
            version = candidate['version']
            version_counts[version] = version_counts.get(version, 0) + 1
        
        # 返回出现次数最多的版本
        most_common_version = max(version_counts, key=version_counts.get)
        return most_common_version
    
    def _merge_fix_method_with_default(self, package_data: List[Dict]) -> str:
        """合并修复方法，为非 SnykDB 来源设置默认值"""
        fix_method_fields = self.field_mappings.get('fix_method', [])
        
        for item in package_data:
            result = item['original_result']
            source = item.get('source', '').lower()
            
            # 只有 SnykDB 来源才可能有真实的 Fix Method
            if source == 'snykdb':
                for field_name in fix_method_fields:
                    fix_method = result.get(field_name)
                    if fix_method and fix_method != "":
                        return fix_method
        
        # 如果没有找到 SnykDB 的 Fix Method，返回默认值
        return "Remove this malicious package from project"
    
    def _calculate_severity(self, confidence_info: Dict) -> str:
        """根据置信度计算严重程度"""
        if confidence_info['high_confidence_count'] >= 2:
            return "high"
        elif confidence_info['high_confidence_count'] >= 1:
            return "medium"
        else:
            return "low"
    
    def save_merged_results(self, merged_results: List[Dict]) -> int:
        """保存合并结果到数据库 - 支持增量更新"""
        if not merged_results:
            return 0
        
        try:
            collection_name = "threat_intelligence"
            collection = self.db.db[collection_name]
            
            inserted_count = 0
            updated_count = 0
            unchanged_count = 0
            
            for merged_item in merged_results:
                package_name = merged_item['package_name']
                package_manager = merged_item['package_manager']
                
                # 查询是否已存在相同的包
                existing_record = collection.find_one({
                    'package_name': package_name,
                    'package_manager': package_manager
                })
                
                current_time = datetime.utcnow().isoformat() + "Z"
                
                if existing_record:
                    # 字段级别合并更新
                    update_fields = {}
                    has_changes = False
                    
                    # 保持不变的字段
                    preserved_fields = {
                        'id': existing_record.get('id'),
                        '_id': existing_record.get('_id'),
                        'metadata': {
                            **merged_item.get('metadata', {}),
                            'created_at': existing_record.get('metadata', {}).get('created_at') or current_time,
                            'last_updated': current_time  # 总是更新这个字段
                        }
                    }
                    
                    # 逐字段比较和合并
                    for key, new_value in merged_item.items():
                        if key in ['id', '_id', 'metadata']:
                            continue  # 这些字段特殊处理
                            
                        existing_value = existing_record.get(key)
                        if existing_value != new_value:
                            update_fields[key] = new_value
                            has_changes = True
                    
                    # 处理metadata字段（除了created_at）
                    existing_metadata = existing_record.get('metadata', {})
                    new_metadata = merged_item.get('metadata', {})
                    
                    for meta_key, meta_value in new_metadata.items():
                        if meta_key == 'created_at':
                            continue  # created_at保持不变
                        
                        existing_meta_value = existing_metadata.get(meta_key)
                        if existing_meta_value != meta_value:
                            has_changes = True
                    
                    # 如果有变化，执行更新
                    if has_changes:
                        # 构建完整的更新数据
                        final_update_data = {**merged_item}
                        final_update_data.update(preserved_fields)
                        final_update_data.pop('_id', None)  # 移除_id，避免更新冲突
                        
                        collection.update_one(
                            {
                                'package_name': package_name,
                                'package_manager': package_manager
                            },
                            {'$set': final_update_data}
                        )
                        updated_count += 1
                    else:
                        unchanged_count += 1
                    
                else:
                    # 插入新记录：created_at和last_updated都是当前时间
                    merged_item['metadata']['created_at'] = current_time
                    merged_item['metadata']['last_updated'] = current_time
                    
                    collection.insert_one(merged_item)
                    inserted_count += 1
            
            # 统计信息输出
            print(f"\n{'='*60}")
            print(f"📊 聚合结果统计")
            print(f"{'='*60}")
            print(f"➕ 新增包数量: {inserted_count}")
            print(f"🔄 更新包数量: {updated_count}")
            print(f"⚪ 不变包数量: {unchanged_count}")
            print(f"📦 处理总数量: {inserted_count + updated_count + unchanged_count}")
            print(f"{'='*60}")
            
            if inserted_count > 0:
                print(f"✨ 发现 {inserted_count} 个新的恶意包")
            if updated_count > 0:
                print(f"🔄 更新了 {updated_count} 个已存在包的信息")
            
            print(f"✅ 聚合完成！")
            return inserted_count + updated_count + unchanged_count
            
        except Exception as e:
            print(f"❌ 保存合并结果时出错: {e}")
            return 0
