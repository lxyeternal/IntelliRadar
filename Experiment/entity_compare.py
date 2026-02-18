#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import os
from typing import Dict, List, Union, Tuple, Set
from collections import defaultdict


def normalize_package_names(names: Union[str, List[str]]) -> List[str]:
    """Normalize package names to a lowercase list"""
    if isinstance(names, str):
        return [names.lower()]
    return [name.lower() for name in names]


def normalize_package_manager(manager: Union[str, List[str]]) -> str:
    """Normalize package manager name"""
    if not manager or (isinstance(manager, list) and (not manager or manager[0] in ["", None])):
        return "other"
    if isinstance(manager, list):
        manager = manager[0]
    manager = manager.lower() if manager else "other"
    # Unify pip and python to pypi
    if manager in ['pip', 'python']:
        return 'pypi'
    return manager


def get_package_name_key(item: dict) -> str:
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


def get_package_manager_key(item: dict) -> str:
    """Get the package manager key from item"""
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

    if process_errors:
        print("\nProcessing error summary:")
        print(f"Total {len(process_errors)} files encountered issues:")
        for filename, error_type, error_msg in process_errors:
            print(f"- File: {filename}")
            print(f"  Error type: {error_type}")
            if error_msg:
                print(f"  Error message: {error_msg}")
        print()

    print("\nPackage deduplication statistics:")
    for manager in package_managers:
        duplicate_packages = [(name, count) for (mgr, name), count in package_counts.items()
                            if mgr == manager and count > 1]
        if duplicate_packages:
            print(f"\nDuplicate packages in {manager} manager:")
            for name, count in sorted(duplicate_packages, key=lambda x: x[1], reverse=True):
                print(f"  - {name}: appeared {count} times")

    return {
        manager: sorted(list(packages))
        for manager, packages in package_managers.items()
    }


def calculate_metrics(groundtruth: Dict[str, List[str]], prediction: Dict[str, List[str]], mode: str = 'all') -> Dict[
    str, float]:
    """Calculate evaluation metrics"""
    gt_packages = set()
    pred_packages = set()

    if mode == 'npm_pypi':
        for manager in ['npm', 'pypi']:
            gt_packages.update(set(groundtruth.get(manager, [])))
            pred_packages.update(set(prediction.get(manager, [])))
    else:
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

    metrics['precision'] = len(correct) / len(pred_packages) if pred_packages else 0.0
    metrics['recall'] = len(correct) / len(gt_packages) if gt_packages else 0.0

    if metrics['precision'] + metrics['recall'] > 0:
        metrics['f1'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    else:
        metrics['f1'] = 0.0

    metrics['unique_correct'] = len(correct)
    metrics['total_unique_groundtruth'] = len(gt_packages)
    metrics['total_unique_prediction'] = len(pred_packages)

    return metrics


def process_localllm_models(base_path: str) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """Process all model and state results under the localllm directory"""
    all_results = {}
    all_states = {'cot', 'cot_fewshot', 'default', 'fewshot'}

    for model in os.listdir(base_path):
        model_path = os.path.join(base_path, model)
        if not os.path.isdir(model_path):
            continue

        model_results = {}
        available_states = set(os.listdir(model_path))

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
    """Print evaluation metrics"""
    print(f"\n{indent}{mode_name}:")
    print(f"{indent}Basic statistics:")
    print(f"{indent}- Groundtruth total packages: {metrics['groundtruth_total']}")
    print(f"{indent}- Prediction total packages: {metrics['prediction_total']}")
    print(f"{indent}- Correct predictions: {metrics['correct_count']}")
    print(f"{indent}- Missed: {metrics['missed_count']}")
    print(f"{indent}- False positives: {metrics['extra_count']}")

    print(f"\n{indent}Evaluation metrics:")
    print(f"{indent}- Precision: {metrics['precision']:.4f}")
    print(f"{indent}- Recall: {metrics['recall']:.4f}")
    print(f"{indent}- F1 Score: {metrics['f1']:.4f}")


def compare_and_print_metrics(groundtruth_results, model_results):
    """Compare and print evaluation metrics for each model and state"""
    print("\n=== Evaluation Metrics ===")

    sorted_models = sorted(model_results.keys())

    for model in sorted_models:
        states = model_results[model]

        print(f"\n{'=' * 50}")
        print(f"Model: {model}")
        print('=' * 50)

        sorted_states = sorted(states.keys())

        state_metrics = {}

        for state in sorted_states:
            prediction = states[state]
            metrics = calculate_metrics(groundtruth_results, prediction, mode='npm_pypi')
            state_metrics[state] = metrics

            indent = "  "
            print(f"\n{indent}State: {state}")
            print(f"{indent}{'-' * 28}")
            print_metrics(metrics, "NPM and PyPI Package Evaluation Results", indent=indent + "  ")

        if len(sorted_states) > 1:
            print(f"\n{indent}F1 score comparison across states:")
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
