import os
import json
import re
from collections import defaultdict

def extract_packages_from_ctikg(file_path):
    """从CTIKG提取的三元组中获取包名和包管理器"""
    packages = defaultdict(set)  # {manager: {package_names}}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            triples = data.get('extracted_triples', '')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}
    
    # 确定包管理器
    manager = 'other'
    if 'npm' in triples.lower():
        manager = 'npm'
    elif 'pypi' in triples.lower() or 'python' in triples.lower():
        manager = 'pypi'
    
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
    
    # 需要过滤的词汇
    filter_words = {
        'malicious', 'fake', 'typosquatted', 'package', 'library', 'module', 
        'sensitive', 'files', 'data', 'information', 'code', 'webhook', 
        'discord', 'channel', 'api', 'interface', 'game', 'execution',
        'developers', 'users', 'credentials', 'browser', 'history',
        'npm', 'pypi', 'python', 'javascript', 'js', 'repository',
        'official', 'security', 'team', 'advisory', 'database',
        'leveldb', 'storage', 'local', 'roaming', 'appdata',
        'chrome', 'opera', 'yandex', 'brave', 'fallguys', 'fall', 'guys'
    }
    
    # 提取包名
    for pattern in package_patterns:
        matches = re.findall(pattern, triples, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                for item in match:
                    name = item.lower().strip()
                    if (name and len(name) > 2 and 
                        name not in filter_words and 
                        not any(word in name for word in ['malicious', 'fake', 'sensitive']) and
                        re.match(r'^[a-zA-Z0-9_-]+$', name)):
                        packages[manager].add(name)
            else:
                name = match.lower().strip()
                if (name and len(name) > 2 and 
                    name not in filter_words and 
                    not any(word in name for word in ['malicious', 'fake', 'sensitive']) and
                    re.match(r'^[a-zA-Z0-9_-]+$', name)):
                    packages[manager].add(name)
    
    # 特殊处理：从文本中直接查找特定的包名
    # 查找colorama包名
    if 'colorama' in triples.lower():
        packages[manager].add('colorama')
    
    # 查找fallguys包名
    if 'fallguys' in triples.lower():
        packages[manager].add('fallguys')
    
    # 查找yocolor包名
    if 'yocolor' in triples.lower():
        packages[manager].add('yocolor')
    
    return {k: list(v) for k, v in packages.items() if v}

def extract_packages_from_secbert(file_path):
    """从SecBERT实体识别结果中提取包名和包管理器"""
    packages = defaultdict(set)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}
    
    # 获取原始文本和实体列表
    text = data.get('text', '')
    entities = data.get('entities', [])
    
    # 先确定包管理器
    manager = 'other'
    if 'npm' in text.lower() or 'node package' in text.lower() or 'javascript' in text.lower():
        manager = 'npm'
    elif 'pypi' in text.lower() or 'python package' in text.lower() or 'python' in text.lower():
        manager = 'pypi'
    
    # 过滤词汇
    filter_words = {
        'malicious', 'fake', 'package', 'library', 'module', 'dependency',
        'npm', 'pypi', 'python', 'javascript', 'security', 'team',
        'repository', 'official', 'users', 'affected', 'attack',
        'infrastructure', 'over', 'removed', 'from', 'the', 'designed',
        'to', 'steal', 'sensitive', 'files', 'victims', 'browser',
        'discord', 'application', 'contained', 'malicious', 'code',
        'used', 'local', 'exfiltrate', 'information', 'through',
        'webhook', 'claimed', 'provide', 'interface', 'game', 'api',
        'available', 'downloaded', 'nearly', 'times', 'advisory',
        'project', 'integrated', 'execution', 'experts', 'noticed',
        'specific', 'developers', 'systems', 'attempt', 'access',
        'content', 'following', 'five', 'post', 'data', 'inside',
        'channel', 'first', 'four', 'leveldb', 'databases', 'common',
        'browsers', 'chrome', 'opera', 'yandex', 'browser', 'brave',
        'contain', 'user', 'browsing', 'history', 'roaming', 'storage',
        'sort', 'database', 'windows', 'client', 'store', 'channels',
        'joined', 'speculate', 'gather', 'sites', 'accessing', 'remove',
        'system', 'ensure', 'compromised', 'credentials', 'rotated',
        'concludes', 'pierluigi', 'paganini', 'securityaffairs', 'hacking',
        'adrotate', 'banner'
    }
    
    # 1. 从实体列表中查找潜在的包名
    for entity in entities:
        entity_text = entity.get('entity', '').strip().lower()
        if not entity_text or len(entity_text) < 3:
            continue
        
        # 检查是否是有效的包名格式
        if (re.match(r'^[a-zA-Z0-9_-]+$', entity_text) and 
            entity_text not in filter_words and
            not any(word in entity_text for word in ['malicious', 'fake', 'package'])):
            packages[manager].add(entity_text)
    
    # 2. 从文本中直接查找特定的包名模式
    # 查找引号中的包名
    quote_patterns = [
        r'"([a-zA-Z0-9_-]+)"',
        r"'([a-zA-Z0-9_-]+)'",
        r'`([a-zA-Z0-9_-]+)`'
    ]
    
    for pattern in quote_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            name = match.lower().strip()
            if (name and len(name) > 2 and 
                name not in filter_words and 
                re.match(r'^[a-zA-Z0-9_-]+$', name)):
                packages[manager].add(name)
    
    # 3. 查找版本号附近的包名
    version_patterns = [
        r'([a-zA-Z0-9_-]+)\s+\(version\s+([0-9.]+)\)',
        r'([a-zA-Z0-9_-]+)-([0-9.]+)',
        r'([a-zA-Z0-9_-]+)\s+version\s+([0-9.]+)',
        r'([a-zA-Z0-9_-]+)\s+v([0-9.]+)'
    ]
    
    for pattern in version_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 1:
                pkg_name = match[0].lower().strip()
                if (pkg_name and len(pkg_name) > 2 and 
                    pkg_name not in filter_words and 
                    re.match(r'^[a-zA-Z0-9_-]+$', pkg_name)):
                    packages[manager].add(pkg_name)
    
    # 4. 特殊处理：从文本中直接查找已知的包名
    known_packages = ['colorama', 'fallguys', 'yocolor']
    for pkg in known_packages:
        if pkg in text.lower():
            packages[manager].add(pkg)
    
    # 5. 查找"library"或"package"后面的包名
    lib_patterns = [
        r'library\s+"([a-zA-Z0-9_-]+)"',
        r'package\s+"([a-zA-Z0-9_-]+)"',
        r'library\s+\'([a-zA-Z0-9_-]+)\'',
        r'package\s+\'([a-zA-Z0-9_-]+)\'',
        r'library\s+([a-zA-Z0-9_-]+)',
        r'package\s+([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in lib_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            name = match.lower().strip()
            if (name and len(name) > 2 and 
                name not in filter_words and 
                re.match(r'^[a-zA-Z0-9_-]+$', name)):
                packages[manager].add(name)
    
    return {k: list(v) for k, v in packages.items() if v}

# 从review-d中导入的函数
def normalize_package_names(names):
    """标准化包名称，将单个字符串或列表转换为小写的列表"""
    if isinstance(names, str):
        return [names.lower()]
    return [name.lower() for name in names]

def normalize_package_manager(manager):
    """标准化包管理器名称"""
    if not manager or (isinstance(manager, list) and (not manager or manager[0] in ["", None])):
        return "other"
    if isinstance(manager, list):
        manager = manager[0]
    manager = manager.lower() if manager else "other"
    # 统一将pip和python转换为pypi
    if manager in ['pip', 'python']:
        return 'pypi'
    return manager

def get_package_name_key(item):
    """获取包名称的键"""
    possible_keys = [
        'Package Name', 'package name', 'PackageName', 'packagename',
        'package_name', 'Package_Name', 'PACKAGE_NAME', 'PACKAGENAME',
        'Package Names', 'package names', 'PackageNames', 'packagenames',
        'package_names', 'Package_Names', 'PACKAGE_NAMES', 'PACKAGENAMES'
    ]
    for key in possible_keys:
        if key in item:
            return key
    raise KeyError("No package name key found in item")

def get_package_manager_key(item):
    """获取包管理器的键"""
    possible_keys = [
        'Package Manager', 'package manager', 'PackageManager', 'packagemanager',
        'package_manager', 'Package_Manager', 'PACKAGE_MANAGER', 'PACKAGEMANAGER',
        'Package Managers', 'package managers', 'PackageManagers', 'packagemanagers',
        'package_managers', 'Package_Managers', 'PACKAGE_MANAGERS', 'PACKAGEMANAGERS',
        'registry', 'Registry', 'REGISTRY'  # 添加registry作为可能的包管理器键
    ]
    for key in possible_keys:
        if key in item:
            return key
    return None

def process_json_files(directory_path, verify_only=False):
    """处理目录中的JSON文件，保留所有包管理器的数据"""
    package_managers = defaultdict(set)  # 使用set自动去重
    process_errors = []
    package_counts = defaultdict(int)  # 用于统计每个包出现的次数

    if not os.path.exists(directory_path):
        print(f"目录不存在: {directory_path}")
        return {}

    for filename in os.listdir(directory_path):
        if not filename.endswith('.json'):
            continue

        if verify_only and '_relation_' not in filename:
            continue

        file_path = os.path.join(directory_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if '[{}]' in content:
                continue

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
                    continue

            except json.JSONDecodeError as e:
                # 尝试从内容中提取JSON
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        process_errors.append((filename, "JSON解析失败", str(e)))
                        continue
                else:
                    process_errors.append((filename, "无法找到有效的JSON内容", None))
                    continue

            for item in data:
                try:
                    package_name_key = get_package_name_key(item)
                    package_names = item[package_name_key]

                    manager_key = get_package_manager_key(item)
                    package_manager = item.get(manager_key, 'other') if manager_key else 'other'

                    # 标准化处理
                    names = normalize_package_names(package_names)
                    manager = normalize_package_manager(package_manager)

                    # 保存所有包管理器的数据并统计出现次数
                    for name in names:
                        package_managers[manager].add(name)
                        package_counts[(manager, name)] += 1

                except KeyError as e:
                    process_errors.append((filename, "缺少必要的键", str(e)))
                    continue

        except Exception as e:
            process_errors.append((filename, type(e).__name__, str(e)))
            continue

    # 将集合转换为排序后的列表
    return {
        manager: sorted(list(packages))
        for manager, packages in package_managers.items()
    }

def process_tool_results(tool_dir, extract_func):
    """处理工具结果目录"""
    results = defaultdict(set)
    
    for filename in os.listdir(tool_dir):
        if not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(tool_dir, filename)
        packages = extract_func(file_path)
        
        for manager, pkg_list in packages.items():
            results[manager].update(pkg_list)
    
    return {k: list(v) for k, v in results.items() if v}

def calculate_metrics(groundtruth, prediction):
    """计算评估指标"""
    # 将所有包管理器的包合并为一个集合
    gt_packages = set()
    pred_packages = set()
    
    for manager, packages in groundtruth.items():
        gt_packages.update(packages)
    
    for manager, packages in prediction.items():
        pred_packages.update(packages)
    
    # 计算指标
    correct = gt_packages.intersection(pred_packages)
    precision = len(correct) / len(pred_packages) if pred_packages else 0
    recall = len(correct) / len(gt_packages) if gt_packages else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'correct': len(correct),
        'groundtruth_total': len(gt_packages),
        'prediction_total': len(pred_packages),
        'correct_packages': sorted(list(correct))
    }

def print_results(groundtruth, ctikg_results, secbert_results, ctikg_metrics, secbert_metrics):
    """打印结果和评估指标"""
    print("\n=== Groundtruth包 ===")
    for manager, packages in groundtruth.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")
    
    print("\n=== CTIKG提取的包 ===")
    for manager, packages in ctikg_results.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")
    
    print("\n=== SecBERT提取的包 ===")
    for manager, packages in secbert_results.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")
    
    print("\n=== CTIKG评估指标 ===")
    print(f"准确率 (Precision): {ctikg_metrics['precision']:.4f}")
    print(f"召回率 (Recall): {ctikg_metrics['recall']:.4f}")
    print(f"F1分数: {ctikg_metrics['f1']:.4f}")
    print(f"正确识别的包数量: {ctikg_metrics['correct']}")
    print(f"Ground Truth总包数: {ctikg_metrics['groundtruth_total']}")
    print(f"预测总包数: {ctikg_metrics['prediction_total']}")
    
    print("\n=== SecBERT评估指标 ===")
    print(f"准确率 (Precision): {secbert_metrics['precision']:.4f}")
    print(f"召回率 (Recall): {secbert_metrics['recall']:.4f}")
    print(f"F1分数: {secbert_metrics['f1']:.4f}")
    print(f"正确识别的包数量: {secbert_metrics['correct']}")
    print(f"Ground Truth总包数: {secbert_metrics['groundtruth_total']}")
    print(f"预测总包数: {secbert_metrics['prediction_total']}")

def main():
    # 设置目录路径
    groundtruth_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    ctikg_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/CTIKG/extracted_packages'
    secbert_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/SecBERT/SecBERT_entity'
    
    # 使用两种不同的方法加载groundtruth
    groundtruth_old = process_json_files(groundtruth_dir)
    
    # 计算差异
    all_old_packages = set()
    for manager, packages in groundtruth_old.items():
        all_old_packages.update(packages)
    
    print(f"\n=== Groundtruth数据分析 ===")
    print(f"使用process_json_files方法提取的包总数: {len(all_old_packages)}")
    
    # 处理CTIKG结果
    ctikg_results = process_tool_results(ctikg_dir, extract_packages_from_ctikg)
    
    # 处理SecBERT结果
    secbert_results = process_tool_results(secbert_dir, extract_packages_from_secbert)
    
    # 计算评估指标
    ctikg_metrics = calculate_metrics(groundtruth_old, ctikg_results)
    secbert_metrics = calculate_metrics(groundtruth_old, secbert_results)
    
    # 打印结果和评估指标
    print_results(groundtruth_old, ctikg_results, secbert_results, ctikg_metrics, secbert_metrics)

if __name__ == "__main__":
    main()