# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : entity_compare
# @Project  : SCC_Intelligence
# Time      : 12/31/24 15:19
# Author    : blue
# version   : python 
# Description：
"""

import json
import os
from typing import Dict, List, Union, Tuple, Set
from collections import defaultdict

# 控制文件处理模式的标志
# 1: 处理所有JSON文件
# 2: 只处理带有"_verify"后缀的JSON文件
PROCESS_MODE = 1  # 可以修改这个值来切换模式


def normalize_package_names(names: Union[str, List[str]]) -> List[str]:
    """标准化包名称，将单个字符串或列表转换为小写的列表"""
    if isinstance(names, str):
        return [names.lower()]
    return [name.lower() for name in names]


def normalize_package_manager(manager: Union[str, List[str]]) -> str:
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


def get_package_name_key(item: dict) -> str:
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


def get_package_manager_key(item: dict) -> str:
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


def process_json_files(directory_path: str, verify_only: bool = False) -> Dict[str, List[str]]:
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

    # 打印汇总信息
    if process_errors:
        print("\n处理错误汇总:")
        print(f"总计 {len(process_errors)} 个文件处理出现问题:")
        for filename, error_type, error_msg in process_errors:
            print(f"- 文件: {filename}")
            print(f"  错误类型: {error_type}")
            if error_msg:
                print(f"  错误信息: {error_msg}")
        print()

    # 打印去重统计信息
    print("\n包去重统计:")
    for manager in package_managers:
        duplicate_packages = [(name, count) for (mgr, name), count in package_counts.items()
                            if mgr == manager and count > 1]
        if duplicate_packages:
            print(f"\n{manager} 管理器中的重复包:")
            for name, count in sorted(duplicate_packages, key=lambda x: x[1], reverse=True):
                print(f"  - {name}: 出现 {count} 次")

    # 将集合转换为排序后的列表
    return {
        manager: sorted(list(packages))
        for manager, packages in package_managers.items()
    }


def process_ablation_versions(base_path: str) -> Dict[str, Dict[str, List[str]]]:
    """处理ablation_prompts/results目录下所有版本的结果"""
    all_results = {}
    
    # 检查基础路径是否存在
    if not os.path.exists(base_path):
        print(f"目录不存在: {base_path}")
        return {}
    
    # 获取所有版本文件夹 (v1, v2, v3, ...)
    version_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and d.startswith('v')]
    
    for version in sorted(version_dirs):
        version_path = os.path.join(base_path, version)
        
        # 获取所有JSON文件，根据PROCESS_MODE决定是处理所有文件还是只处理_verify文件
        all_json_files = [f for f in os.listdir(version_path) if f.endswith('.json')]
        
        if PROCESS_MODE == 2:
            # 只处理带有"_verify"后缀的文件
            json_files = [f for f in all_json_files if '_verify' in f]
            print(f"\n{version} - 只处理_verify文件: 找到 {len(json_files)}/{len(all_json_files)} 个文件")
        else:
            # 处理所有JSON文件
            json_files = all_json_files
            print(f"\n{version} - 处理所有JSON文件: 找到 {len(json_files)} 个文件")
        
        # 对于V1-V3，只关注包名，不考虑包管理器
        if version in ['v1', 'v2', 'v3']:
            all_packages = set()  # 所有包名，不区分包管理器
            process_errors = []
            processed_files = 0
            
            for filename in json_files:
                file_path = os.path.join(version_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or content == '{}' or '[{}]' in content:
                        continue
                    
                    try:
                        parsed_json = json.loads(content)
                        
                        # 处理单个JSON对象
                        if isinstance(parsed_json, dict):
                            data = [parsed_json]
                        # 处理JSON数组
                        elif isinstance(parsed_json, list):
                            data = parsed_json
                        else:
                            continue
                        
                        for item in data:
                            try:
                                # 尝试获取包名称
                                package_names = None
                                
                                # 首先尝试标准键
                                try:
                                    package_name_key = get_package_name_key(item)
                                    package_names = item[package_name_key]
                                except KeyError:
                                    # 然后尝试直接使用package_name (v1特殊情况)
                                    if 'package_name' in item:
                                        package_names = item['package_name']
                                    else:
                                        raise KeyError("No package name found")
                                
                                # 标准化处理
                                names = normalize_package_names(package_names)
                                
                                # 保存所有包名
                                for name in names:
                                    all_packages.add(name)
                                
                                processed_files += 1
                                    
                            except KeyError as e:
                                process_errors.append((filename, "缺少必要的键", str(e)))
                                continue
                    
                    except json.JSONDecodeError as e:
                        process_errors.append((filename, "JSON解析失败", str(e)))
                        continue
                
                except Exception as e:
                    process_errors.append((filename, type(e).__name__, str(e)))
                    continue
            
            # 打印处理错误
            if process_errors:
                print(f"\n{version} 处理错误汇总:")
                print(f"总计 {len(process_errors)} 个文件处理出现问题:")
                for filename, error_type, error_msg in process_errors[:10]:  # 只显示前10个错误
                    print(f"- 文件: {filename}")
                    print(f"  错误类型: {error_type}")
                    if error_msg:
                        print(f"  错误信息: {error_msg}")
                if len(process_errors) > 10:
                    print(f"  ... 还有 {len(process_errors) - 10} 个错误未显示")
            
            # 对于V1-V3，我们将所有包名放在npm和pypi两个包管理器下
            # 这样可以确保在计算指标时能够正确比较
            all_results[version] = {
                'npm': sorted(list(all_packages)),
                'pypi': sorted(list(all_packages))
            }
            
            # 打印当前版本的包统计
            print(f"\n{version} 包统计:")
            print(f"  - 成功处理的文件数: {processed_files}/{len(json_files)}")
            print(f"  - 总包数: {len(all_packages)} 个包")
        
        else:
            # 对于其他版本，保持原来的逻辑，区分包管理器
            package_managers = defaultdict(set)
            process_errors = []
            package_counts = defaultdict(int)
            processed_files = 0
            
            for filename in json_files:
                file_path = os.path.join(version_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or content == '{}' or '[{}]' in content:
                        continue
                    
                    try:
                        parsed_json = json.loads(content)
                        
                        # 处理单个JSON对象
                        if isinstance(parsed_json, dict):
                            data = [parsed_json]
                        # 处理JSON数组
                        elif isinstance(parsed_json, list):
                            data = parsed_json
                        else:
                            continue
                        
                        for item in data:
                            try:
                                # 尝试获取包名称
                                try:
                                    package_name_key = get_package_name_key(item)
                                    package_names = item[package_name_key]
                                except KeyError:
                                    # 对于v1可能直接使用package_name
                                    if 'package_name' in item:
                                        package_names = item['package_name']
                                    else:
                                        raise KeyError("No package name found")
                                
                                # 尝试获取包管理器
                                manager_key = get_package_manager_key(item)
                                package_manager = item.get(manager_key, 'other') if manager_key else 'other'
                                
                                # 标准化处理
                                names = normalize_package_names(package_names)
                                manager = normalize_package_manager(package_manager)
                                
                                # 保存所有包管理器的数据并统计出现次数
                                for name in names:
                                    package_managers[manager].add(name)
                                    package_counts[(manager, name)] += 1
                                
                                processed_files += 1
                                    
                            except KeyError as e:
                                process_errors.append((filename, "缺少必要的键", str(e)))
                                continue
                    
                    except json.JSONDecodeError as e:
                        process_errors.append((filename, "JSON解析失败", str(e)))
                        continue
                
                except Exception as e:
                    process_errors.append((filename, type(e).__name__, str(e)))
                    continue
            
            # 打印处理错误
            if process_errors:
                print(f"\n{version} 处理错误汇总:")
                print(f"总计 {len(process_errors)} 个文件处理出现问题:")
                for filename, error_type, error_msg in process_errors[:10]:  # 只显示前10个错误
                    print(f"- 文件: {filename}")
                    print(f"  错误类型: {error_type}")
                    if error_msg:
                        print(f"  错误信息: {error_msg}")
                if len(process_errors) > 10:
                    print(f"  ... 还有 {len(process_errors) - 10} 个错误未显示")
            
            # 将集合转换为排序后的列表
            all_results[version] = {
                manager: sorted(list(packages))
                for manager, packages in package_managers.items()
            }
            
            # 打印当前版本的包统计
            print(f"\n{version} 包统计:")
            print(f"  - 成功处理的文件数: {processed_files}/{len(json_files)}")
            for manager, packages in all_results[version].items():
                print(f"  - {manager}: {len(packages)} 个包")
    
    return all_results


def calculate_metrics(groundtruth: Dict[str, List[str]], prediction: Dict[str, List[str]], mode: str = 'all') -> Dict[
    str, float]:
    """计算评估指标"""
    gt_packages = set()
    pred_packages = set()

    if mode == 'npm_pypi':
        # 只处理npm和pypi的包
        for manager in ['npm', 'pypi']:
            # 确保添加之前已经去重
            gt_packages.update(set(groundtruth.get(manager, [])))
            pred_packages.update(set(prediction.get(manager, [])))
    else:
        # 处理所有包管理器的包
        for packages in groundtruth.values():
            gt_packages.update(set(packages))
        for packages in prediction.values():
            pred_packages.update(set(packages))

    correct = gt_packages.intersection(pred_packages)
    missed = gt_packages - pred_packages
    extra = pred_packages - gt_packages

    metrics = {
        'correct_count': len(correct),
        'missed_count': len(missed),
        'extra_count': len(extra),
        'groundtruth_total': len(gt_packages),
        'prediction_total': len(pred_packages)
    }

    # 计算评估指标
    metrics['precision'] = len(correct) / len(pred_packages) if pred_packages else 0.0
    metrics['recall'] = len(correct) / len(gt_packages) if gt_packages else 0.0

    if metrics['precision'] + metrics['recall'] > 0:
        metrics['f1'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    else:
        metrics['f1'] = 0.0

    # 添加去重信息
    metrics['unique_correct'] = len(correct)
    metrics['total_unique_groundtruth'] = len(gt_packages)
    metrics['total_unique_prediction'] = len(pred_packages)

    return metrics


def process_localllm_models(base_path: str) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """处理localllm目录下所有模型和状态的结果"""
    all_results = {}
    all_states = {'cot', 'cot_fewshot', 'default', 'fewshot'}  # 所有可能的状态

    for model in os.listdir(base_path):
        model_path = os.path.join(base_path, model)
        if not os.path.isdir(model_path):
            continue

        model_results = {}
        available_states = set(os.listdir(model_path))  # 获取当前模型实际有的状态

        # 处理每个状态
        for state in all_states.intersection(available_states):
            state_path = os.path.join(model_path, state)
            if not os.path.isdir(state_path):
                continue

            results = process_json_files(state_path, verify_only=True)
            if results:
                model_results[state] = results

        if model_results:
            all_results[model] = model_results

    return all_results


def print_metrics(metrics: Dict[str, float], mode_name: str, indent: str = ""):
    """打印评估指标"""
    print(f"\n{indent}{mode_name}:")
    print(f"{indent}基本统计:")
    print(f"{indent}- Groundtruth总包数: {metrics['groundtruth_total']}")
    print(f"{indent}- 预测总包数: {metrics['prediction_total']}")
    print(f"{indent}- 正确预测数: {metrics['correct_count']}")
    print(f"{indent}- 漏检数: {metrics['missed_count']}")
    print(f"{indent}- 误检数: {metrics['extra_count']}")

    print(f"\n{indent}评估指标:")
    print(f"{indent}- 准确率 (Precision): {metrics['precision']:.4f}")
    print(f"{indent}- 召回率 (Recall): {metrics['recall']:.4f}")
    print(f"{indent}- F1分数: {metrics['f1']:.4f}")


def compare_and_print_metrics(groundtruth_results, model_results):
    """比较并打印每个模型和状态的评估指标"""
    print("\n=== 评估指标 ===")

    # 按模型名称排序
    sorted_models = sorted(model_results.keys())

    for model in sorted_models:
        states = model_results[model]

        # 打印模型分隔线和名称
        print(f"\n{'=' * 50}")
        print(f"模型: {model}")
        print('=' * 50)

        # 按状态名称排序
        sorted_states = sorted(states.keys())

        # 存储每个状态的指标用于比较
        state_metrics = {}

        # 遍历每个状态
        for state in sorted_states:
            prediction = states[state]
            metrics = calculate_metrics(groundtruth_results, prediction, mode='npm_pypi')
            state_metrics[state] = metrics

            # 使用缩进来改善可读性
            indent = "  "
            print(f"\n{indent}状态: {state}")
            print(f"{indent}{'-' * 28}")
            print_metrics(metrics, "NPM和PyPI包的评估结果", indent=indent + "  ")

        # 如果有多个状态，打印比较结果
        if len(sorted_states) > 1:
            print(f"\n{indent}状态间F1分数比较:")
            for state in sorted_states:
                f1 = state_metrics[state]['f1']
                print(f"{indent}- {state}: {f1:.4f}")


def compare_and_print_ablation_metrics(groundtruth_results, ablation_results):
    """比较并打印不同版本的评估指标"""
    print("\n=== Ablation Study 评估指标 ===")
    print(f"处理模式: {'只处理_verify文件' if PROCESS_MODE == 2 else '处理所有JSON文件'}")

    # 按版本排序
    sorted_versions = sorted(ablation_results.keys())
    
    # 存储每个版本的指标用于比较
    version_metrics = {}
    
    # 遍历每个版本
    for version in sorted_versions:
        prediction = ablation_results[version]
        metrics = calculate_metrics(groundtruth_results, prediction, mode='npm_pypi')
        version_metrics[version] = metrics
        
        # 打印版本分隔线和名称
        print(f"\n{'=' * 50}")
        print(f"版本: {version}")
        print('=' * 50)
        
        # 使用缩进来改善可读性
        indent = "  "
        print_metrics(metrics, "NPM和PyPI包的评估结果", indent=indent)
    
    # 打印版本间比较结果
    print(f"\n{'=' * 50}")
    print("版本间F1分数比较:")
    print('=' * 50)
    
    for version in sorted_versions:
        metrics = version_metrics[version]
        print(f"- {version}:")
        print(f"  - 准确率: {metrics['precision']:.4f}")
        print(f"  - 召回率: {metrics['recall']:.4f}")
        print(f"  - F1分数: {metrics['f1']:.4f}")
        print(f"  - 正确/总数: {metrics['correct_count']}/{metrics['prediction_total']}")


def main():
    # 原始groundtruth路径
    groundtruth_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    groundtruth_results = process_json_files(groundtruth_path)
    
    # ablation study路径
    ablation_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/review-d/ablcation_prompts/results'
    ablation_results = process_ablation_versions(ablation_path)
    
    # 比较并打印ablation study的评估指标
    compare_and_print_ablation_metrics(groundtruth_results, ablation_results)


if __name__ == "__main__":
    main()