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
        'package_managers', 'Package_Managers', 'PACKAGE_MANAGERS', 'PACKAGEMANAGERS'
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


def main():
    groundtruth_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    groundtruth_results = process_json_files(groundtruth_path)

    localllm_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq3/localllm'
    localllm_results = process_localllm_models(localllm_path)

    compare_and_print_metrics(groundtruth_results, localllm_results)


if __name__ == "__main__":
    main()