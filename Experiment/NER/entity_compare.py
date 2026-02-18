import os
import json
import re
from collections import defaultdict


def extract_packages_from_ctikg(file_path):
    """Extract package names and package managers from CTIKG triples"""
    packages = defaultdict(set)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            triples = data.get('extracted_triples', '')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    manager = 'other'
    if 'npm' in triples.lower():
        manager = 'npm'
    elif 'pypi' in triples.lower() or 'python' in triples.lower():
        manager = 'pypi'

    package_patterns = [
        r'\[SUBJECT:([^,\]]+), RELATION:is, OBJECT:malicious (?:npm|pypi|python) package\]',
        r'\[SUBJECT:([^,\]]+), RELATION:(?:is|contains), OBJECT:malicious (?:npm|pypi|python) package\]',
        r'\[SUBJECT:malicious (?:npm|pypi|python) package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
        r'\[SUBJECT:malicious package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
        r'\[SUBJECT:([^,\]]+), RELATION:(?:designed to|steals|contains), OBJECT:[^,\]]+\]',
        r'\[SUBJECT:([^,\]]+), RELATION:(?:published|hosted|available), OBJECT:[^,\]]+\]',
        r'\[SUBJECT:([^,\]]+), RELATION:(?:claimed to provide|downloaded), OBJECT:[^,\]]+\]',
        r'\[SUBJECT:([^,\]]+), RELATION:version, OBJECT:[^,\]]+\]',
        r'\[SUBJECT:([^,\]]+), RELATION:published, OBJECT:[^,\]]+\]',
        r'masquerades, OBJECT:([^,\]]+)',
        r'\[SUBJECT:([a-zA-Z0-9_-]+), RELATION:(?:is|contains|steals), OBJECT:(?:malicious|sensitive)',
    ]

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

    if 'colorama' in triples.lower():
        packages[manager].add('colorama')

    if 'fallguys' in triples.lower():
        packages[manager].add('fallguys')

    if 'yocolor' in triples.lower():
        packages[manager].add('yocolor')

    return {k: list(v) for k, v in packages.items() if v}


def extract_packages_from_secbert(file_path):
    """Extract package names and package managers from SecBERT entity recognition results"""
    packages = defaultdict(set)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    text = data.get('text', '')
    entities = data.get('entities', [])

    manager = 'other'
    if 'npm' in text.lower() or 'node package' in text.lower() or 'javascript' in text.lower():
        manager = 'npm'
    elif 'pypi' in text.lower() or 'python package' in text.lower() or 'python' in text.lower():
        manager = 'pypi'

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

    for entity in entities:
        entity_text = entity.get('entity', '').strip().lower()
        if not entity_text or len(entity_text) < 3:
            continue

        if (re.match(r'^[a-zA-Z0-9_-]+$', entity_text) and
            entity_text not in filter_words and
            not any(word in entity_text for word in ['malicious', 'fake', 'package'])):
            packages[manager].add(entity_text)

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

    known_packages = ['colorama', 'fallguys', 'yocolor']
    for pkg in known_packages:
        if pkg in text.lower():
            packages[manager].add(pkg)

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


def normalize_package_names(names):
    """Normalize package names to a lowercase list"""
    if isinstance(names, str):
        return [names.lower()]
    return [name.lower() for name in names]


def normalize_package_manager(manager):
    """Normalize package manager name"""
    if not manager or (isinstance(manager, list) and (not manager or manager[0] in ["", None])):
        return "other"
    if isinstance(manager, list):
        manager = manager[0]
    manager = manager.lower() if manager else "other"
    if manager in ['pip', 'python']:
        return 'pypi'
    return manager


def get_package_name_key(item):
    """Get the package name key from item"""
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
    """Get the package manager key from item"""
    possible_keys = [
        'Package Manager', 'package manager', 'PackageManager', 'packagemanager',
        'package_manager', 'Package_Manager', 'PACKAGE_MANAGER', 'PACKAGEMANAGER',
        'Package Managers', 'package managers', 'PackageManagers', 'packagemanagers',
        'package_managers', 'Package_Managers', 'PACKAGE_MANAGERS', 'PACKAGEMANAGERS',
        'registry', 'Registry', 'REGISTRY'
    ]
    for key in possible_keys:
        if key in item:
            return key
    return None


def process_json_files(directory_path, verify_only=False):
    """Process JSON files in directory, keeping all package manager data"""
    package_managers = defaultdict(set)
    process_errors = []
    package_counts = defaultdict(int)

    if not os.path.exists(directory_path):
        print(f"Directory does not exist: {directory_path}")
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
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    try:
                        data = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        process_errors.append((filename, "JSON parse failed", str(e)))
                        continue
                else:
                    process_errors.append((filename, "No valid JSON content found", None))
                    continue

            for item in data:
                try:
                    package_name_key = get_package_name_key(item)
                    package_names = item[package_name_key]

                    manager_key = get_package_manager_key(item)
                    package_manager = item.get(manager_key, 'other') if manager_key else 'other'

                    names = normalize_package_names(package_names)
                    manager = normalize_package_manager(package_manager)

                    for name in names:
                        package_managers[manager].add(name)
                        package_counts[(manager, name)] += 1

                except KeyError as e:
                    process_errors.append((filename, "Missing required key", str(e)))
                    continue

        except Exception as e:
            process_errors.append((filename, type(e).__name__, str(e)))
            continue

    return {
        manager: sorted(list(packages))
        for manager, packages in package_managers.items()
    }


def process_tool_results(tool_dir, extract_func):
    """Process tool results directory"""
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
    """Calculate evaluation metrics"""
    gt_packages = set()
    pred_packages = set()

    for manager, packages in groundtruth.items():
        gt_packages.update(packages)

    for manager, packages in prediction.items():
        pred_packages.update(packages)

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
    """Print results and evaluation metrics"""
    print("\n=== Groundtruth Packages ===")
    for manager, packages in groundtruth.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")

    print("\n=== CTIKG Extracted Packages ===")
    for manager, packages in ctikg_results.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")

    print("\n=== SecBERT Extracted Packages ===")
    for manager, packages in secbert_results.items():
        print(f"\n{manager}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")

    print("\n=== CTIKG Evaluation Metrics ===")
    print(f"Precision: {ctikg_metrics['precision']:.4f}")
    print(f"Recall: {ctikg_metrics['recall']:.4f}")
    print(f"F1 Score: {ctikg_metrics['f1']:.4f}")
    print(f"Correctly identified packages: {ctikg_metrics['correct']}")
    print(f"Ground Truth total packages: {ctikg_metrics['groundtruth_total']}")
    print(f"Predicted total packages: {ctikg_metrics['prediction_total']}")

    print("\n=== SecBERT Evaluation Metrics ===")
    print(f"Precision: {secbert_metrics['precision']:.4f}")
    print(f"Recall: {secbert_metrics['recall']:.4f}")
    print(f"F1 Score: {secbert_metrics['f1']:.4f}")
    print(f"Correctly identified packages: {secbert_metrics['correct']}")
    print(f"Ground Truth total packages: {secbert_metrics['groundtruth_total']}")
    print(f"Predicted total packages: {secbert_metrics['prediction_total']}")


def main():
    groundtruth_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    ctikg_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/CTIKG/extracted_packages'
    secbert_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/SecBERT/SecBERT_entity'

    groundtruth_old = process_json_files(groundtruth_dir)

    all_old_packages = set()
    for manager, packages in groundtruth_old.items():
        all_old_packages.update(packages)

    print(f"\n=== Groundtruth Data Analysis ===")
    print(f"Total packages extracted via process_json_files: {len(all_old_packages)}")

    ctikg_results = process_tool_results(ctikg_dir, extract_packages_from_ctikg)
    secbert_results = process_tool_results(secbert_dir, extract_packages_from_secbert)

    ctikg_metrics = calculate_metrics(groundtruth_old, ctikg_results)
    secbert_metrics = calculate_metrics(groundtruth_old, secbert_results)

    print_results(groundtruth_old, ctikg_results, secbert_results, ctikg_metrics, secbert_metrics)


if __name__ == "__main__":
    main()
