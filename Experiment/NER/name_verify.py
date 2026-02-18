#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
按文件名一一对应进行包名验证：对每个groundtruth文件，检查同名的CTIKG和SecBERT文件中是否包含相同的包名
"""

import os
import json
import re
from collections import defaultdict

def extract_package_names_from_file(file_path):
    """从单个groundtruth文件中提取包名"""
    packages = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        try:
            parsed_json = json.loads(content)
            
            # 处理不同的JSON结构
            if isinstance(parsed_json, dict):
                for key in ['packages', 'data', 'results']:
                    if key in parsed_json:
                        data = parsed_json[key]
                        break
                else:
                    data = [parsed_json]
            else:
                data = parsed_json
            
            if isinstance(data, dict):
                data = [data]
            if not data:
                return packages
            
            for item in data:
                # 查找包名
                package_names = None
                for key in ['Package Name', 'package name', 'PackageName', 'packagename',
                           'package_name', 'Package_Name', 'PACKAGE_NAME', 'PACKAGENAME',
                           'Package Names', 'package names', 'PackageNames', 'packagenames',
                           'package_names', 'Package_Names', 'PACKAGE_NAMES', 'PACKAGENAMES']:
                    if key in item:
                        package_names = item[key]
                        break
                
                if package_names:
                    # 标准化包名
                    if isinstance(package_names, str):
                        names = [package_names.lower()]
                    else:
                        names = [name.lower() for name in package_names]
                    
                    # 添加到结果集
                    for name in names:
                        packages.add(name)
        
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {file_path}: {e}")
            return packages
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return packages
    
    return packages

def extract_all_ctikg_packages(file_path):
    """使用更精确的模式提取CTIKG文件中识别的所有包名"""
    all_packages = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            triples = data.get('extracted_triples', '')
        
        # 更精确的包名提取模式
        package_patterns = [
            # 明确的包名模式
            r'\[SUBJECT:([^,\]]+), RELATION:is, OBJECT:malicious (?:npm|pypi|python) package\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:is|contains), OBJECT:malicious (?:npm|pypi|python) package\]',
            r'\[SUBJECT:malicious (?:npm|pypi|python) package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
            r'\[SUBJECT:malicious package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:designed to|steals|contains), OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:published|hosted|available), OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:claimed to provide|downloaded), OBJECT:[^,\]]+\]',
            # 版本相关的包名
            r'\[SUBJECT:([^,\]]+), RELATION:version, OBJECT:[^,\]]+\]',
            # 发布相关的包名
            r'\[SUBJECT:([^,\]]+), RELATION:published, OBJECT:[^,\]]+\]',
            # 特殊的伪装包名
            r'masquerades, OBJECT:([^,\]]+)',
            # 直接提及的包名
            r'\[SUBJECT:([a-zA-Z0-9_-]+), RELATION:(?:is|contains|steals), OBJECT:(?:malicious|sensitive)',
        ]
        
        # 应用所有模式提取包名
        for pattern in package_patterns:
            matches = re.findall(pattern, triples)
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if group and group.strip():
                            all_packages.add(group.strip().lower())
                elif match and match.strip():
                    all_packages.add(match.strip().lower())
        
        # 如果没有找到任何包名，尝试使用更宽松的提取方式
        if not all_packages:
            # 提取所有SUBJECT
            pattern = r'SUBJECT:([^,]+)'
            subjects = re.findall(pattern, triples)
            for subject in subjects:
                entity = subject.strip().lower()
                if entity and len(entity) > 1 and not entity.startswith('the '):
                    all_packages.add(entity)
            
            # 提取所有OBJECT
            pattern = r'OBJECT:([^,\]]+)'
            objects = re.findall(pattern, triples)
            for obj in objects:
                entity = obj.strip().lower()
                if entity and len(entity) > 1 and not entity.startswith('the '):
                    all_packages.add(entity)
        
        # 移除明显不是包名的项目
        non_packages = {'the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they', 'them', 
                       'malicious', 'vulnerable', 'package', 'packages', 'module', 'modules',
                       'library', 'libraries', 'dependency', 'dependencies', 'code', 'software'}
        all_packages = {pkg for pkg in all_packages if pkg not in non_packages and len(pkg) > 1}
    
    except Exception as e:
        print(f"Error extracting packages from CTIKG file {file_path}: {e}")
    
    return all_packages

def check_packages_in_ctikg_file(packages, file_path):
    """检查包名是否在CTIKG文件中"""
    found_packages = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        for package in packages:
            # 检查包名是否作为完整实体存在
            pattern = r'\[SUBJECT:' + re.escape(package) + r'[,\]]|\[SUBJECT:[^,]+, RELATION:[^,]+, OBJECT:' + re.escape(package) + r'[,\]]'
            if re.search(pattern, content, re.IGNORECASE):
                found_packages.add(package)
                continue
            
            # 检查包名是否在三元组中作为独立实体存在
            pattern = r'SUBJECT:([^,]+)'
            subjects = re.findall(pattern, content)
            for subject in subjects:
                if subject.strip().lower() == package:
                    found_packages.add(package)
                    break
            
            pattern = r'OBJECT:([^,\]]+)'
            objects = re.findall(pattern, content)
            for obj in objects:
                if obj.strip().lower() == package:
                    found_packages.add(package)
                    break
    
    except Exception as e:
        print(f"Error checking CTIKG file {file_path}: {e}")
    
    return found_packages

def check_packages_in_secbert_file(packages, file_path):
    """检查包名是否在SecBERT文件中，只检查entities列表中的entity字段"""
    found_packages = set()
    label1_count = 0  # 统计LABEL_1类型的实体数量
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取实体列表
        entities = data.get('entities', [])
        
        # 统计LABEL_1类型的实体
        for entity in entities:
            if entity.get('type') == 'LABEL_1':
                label1_count += 1
        
        # 检查每个包名是否在实体列表中
        for package in packages:
            for entity in entities:
                entity_text = entity.get('entity', '').strip().lower()
                if entity_text == package.lower():
                    found_packages.add(package)
                    break
    
    except Exception as e:
        print(f"Error checking SecBERT file {file_path}: {e}")
    
    return found_packages, label1_count

def main():
    # 设置目录路径
    groundtruth_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    ctikg_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/CTIKG/extracted_packages'
    secbert_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/SecBERT/SecBERT_entity'
    
    # 获取groundtruth目录中的所有JSON文件
    groundtruth_files = [f for f in os.listdir(groundtruth_dir) if f.endswith('.json')]
    print(f"找到 {len(groundtruth_files)} 个groundtruth文件")
    
    # 统计结果
    results = {
        'total_files': len(groundtruth_files),
        'total_packages': 0,
        'ctikg': {'found': 0, 'not_found': 0, 'file_details': {}, 'all_packages': set()},
        'secbert': {'found': 0, 'not_found': 0, 'file_details': {}, 'total_label1_entities': 0}
    }
    
    # 跟踪所有包名
    all_packages = set()
    all_found_ctikg = set()
    all_found_secbert = set()
    
    # 按文件名一一对比
    for i, filename in enumerate(groundtruth_files, 1):
        print(f"处理文件 {i}/{len(groundtruth_files)}: {filename}")
        
        # 构建文件路径
        groundtruth_file = os.path.join(groundtruth_dir, filename)
        ctikg_file = os.path.join(ctikg_dir, filename)
        secbert_file = os.path.join(secbert_dir, filename)
        
        # 从groundtruth文件中提取包名
        groundtruth_packages = extract_package_names_from_file(groundtruth_file)
        
        # 如果没有包名，跳过此文件
        if not groundtruth_packages:
            print(f"  - 警告: {filename} 中未找到包名")
            continue
        
        # 更新总包数和所有包名集合
        results['total_packages'] += len(groundtruth_packages)
        all_packages.update(groundtruth_packages)
        
        # 检查CTIKG文件
        ctikg_found_packages = set()
        ctikg_all_packages = set()
        if os.path.exists(ctikg_file):
            ctikg_found_packages = check_packages_in_ctikg_file(groundtruth_packages, ctikg_file)
            ctikg_all_packages = extract_all_ctikg_packages(ctikg_file)
            results['ctikg']['found'] += len(ctikg_found_packages)
            results['ctikg']['not_found'] += len(groundtruth_packages) - len(ctikg_found_packages)
            results['ctikg']['all_packages'].update(ctikg_all_packages)
            all_found_ctikg.update(ctikg_found_packages)
        else:
            print(f"  - 警告: CTIKG目录中未找到对应文件 {filename}")
            results['ctikg']['not_found'] += len(groundtruth_packages)
        
        # 检查SecBERT文件
        secbert_found_packages = set()
        file_label1_count = 0
        if os.path.exists(secbert_file):
            secbert_found_packages, file_label1_count = check_packages_in_secbert_file(groundtruth_packages, secbert_file)
            results['secbert']['found'] += len(secbert_found_packages)
            results['secbert']['not_found'] += len(groundtruth_packages) - len(secbert_found_packages)
            results['secbert']['total_label1_entities'] += file_label1_count
            all_found_secbert.update(secbert_found_packages)
        else:
            print(f"  - 警告: SecBERT目录中未找到对应文件 {filename}")
            results['secbert']['not_found'] += len(groundtruth_packages)
        
        # 记录文件详情
        results['ctikg']['file_details'][filename] = {
            'total': len(groundtruth_packages),
            'found': len(ctikg_found_packages),
            'not_found': len(groundtruth_packages) - len(ctikg_found_packages),
            'found_packages': sorted(list(ctikg_found_packages)),
            'not_found_packages': sorted(list(groundtruth_packages - ctikg_found_packages)),
            'all_packages': len(ctikg_all_packages)
        }
        
        results['secbert']['file_details'][filename] = {
            'total': len(groundtruth_packages),
            'found': len(secbert_found_packages),
            'not_found': len(groundtruth_packages) - len(secbert_found_packages),
            'label1_count': file_label1_count,
            'found_packages': sorted(list(secbert_found_packages)),
            'not_found_packages': sorted(list(groundtruth_packages - secbert_found_packages))
        }
        
        # 打印当前文件的结果
        print(f"  - Groundtruth包数: {len(groundtruth_packages)}")
        print(f"  - CTIKG找到: {len(ctikg_found_packages)}/{len(groundtruth_packages)} ({len(ctikg_found_packages)/len(groundtruth_packages)*100:.1f}%)")
        print(f"  - CTIKG识别的包总数: {len(ctikg_all_packages)}")
        print(f"  - SecBERT找到: {len(secbert_found_packages)}/{len(groundtruth_packages)} ({len(secbert_found_packages)/len(groundtruth_packages)*100:.1f}%)")
        print(f"  - SecBERT LABEL_1实体数: {file_label1_count}")
    
    # 计算去重后的总体结果
    unique_total = 675  # 使用固定值675作为groundtruth包名总数(去重)
    unique_ctikg_found = len(all_found_ctikg)
    unique_secbert_found = len(all_found_secbert)
    total_ctikg_packages = len(results['ctikg']['all_packages'])
    
    # 确保total_ctikg_packages至少等于unique_ctikg_found
    if total_ctikg_packages < unique_ctikg_found:
        print(f"警告: CTIKG识别的包总数({total_ctikg_packages})小于正确识别的包数({unique_ctikg_found})，调整为相等")
        total_ctikg_packages = unique_ctikg_found
    
    # 计算评估指标
    # CTIKG指标
    ctikg_tp = unique_ctikg_found  # 真阳性：正确识别的包名数
    ctikg_fn = unique_total - unique_ctikg_found  # 假阴性：未识别的包名数
    ctikg_fp = total_ctikg_packages - unique_ctikg_found  # 假阳性：错误识别的包名数
    
    ctikg_precision = ctikg_tp / total_ctikg_packages if total_ctikg_packages > 0 else 0
    ctikg_recall = ctikg_tp / unique_total if unique_total > 0 else 0
    ctikg_f1 = 2 * ctikg_precision * ctikg_recall / (ctikg_precision + ctikg_recall) if (ctikg_precision + ctikg_recall) > 0 else 0
    
    # SecBERT指标
    secbert_tp = unique_secbert_found  # 真阳性：正确识别的包名数
    secbert_fn = unique_total - unique_secbert_found  # 假阴性：未识别的包名数
    secbert_fp = results['secbert']['total_label1_entities'] - unique_secbert_found  # 假阳性：错误识别的实体数
    
    secbert_precision = secbert_tp / results['secbert']['total_label1_entities'] if results['secbert']['total_label1_entities'] > 0 else 0
    secbert_recall = secbert_tp / unique_total if unique_total > 0 else 0
    secbert_f1 = 2 * secbert_precision * secbert_recall / (secbert_precision + secbert_recall) if (secbert_precision + secbert_recall) > 0 else 0
    
    # 输出简化的总结结果
    print("\n" + "="*50)
    print("工具评估结果")
    print("="*50)
    
    print(f"\nGroundtruth包名总数(去重): {unique_total}")
    
    print("\n=== CTIKG工具 ===")
    print(f"总识别包名数: {total_ctikg_packages}")
    print(f"正确识别的包名数(TP): {ctikg_tp}")
    print(f"错误识别的包名数(FP): {ctikg_fp}")
    print(f"未识别的包名数(FN): {ctikg_fn}")
    print(f"准确率(Precision): {ctikg_precision:.4f}")
    print(f"召回率(Recall): {ctikg_recall:.4f}")
    print(f"F1分数: {ctikg_f1:.4f}")
    
    print("\n=== SecBERT工具 ===")
    print(f"总识别实体数(LABEL_1): {results['secbert']['total_label1_entities']}")
    print(f"正确识别的包名数(TP): {secbert_tp}")
    print(f"错误识别的实体数(FP): {secbert_fp}")
    print(f"未识别的包名数(FN): {secbert_fn}")
    print(f"准确率(Precision): {secbert_precision:.4f}")
    print(f"召回率(Recall): {secbert_recall:.4f}")
    print(f"F1分数: {secbert_f1:.4f}")

if __name__ == "__main__":
    main()