# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : entity_parse
# @Project  : SCC_Intelligence
# Time      : 1/5/25 12:54
# Author    : blue
# version   : python 
# Description：
"""

# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : entity_parse
# @Project  : SCC_Intelligence
# Time      : 1/5/25 12:54
# Author    : blue
# version   : python 
# Description：
"""

import os
import json
from collections import defaultdict, Counter
from copy import deepcopy


def normalize_package_manager(pkg_manager):
    """标准化包管理器名称"""
    if not pkg_manager or pkg_manager.lower() in ['unknown', 'n/a']:
        return 'other'

    pkg_manager = pkg_manager.lower()
    if pkg_manager in ['pypi', 'python', 'pip']:
        return 'pypi'
    return pkg_manager


def load_pagelinks_data(waiting_path, collected_path):
    """加载pagelinks数据，返回时间戳到post_date和source_link的映射"""
    timestamp_data = {}

    # 处理两个文件
    for file_path in [waiting_path, collected_path]:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:  # 确保有足够的列
                        timestamp = parts[0].strip()
                        post_date = parts[2].strip()
                        source_link = parts[3].strip()
                        timestamp_data[timestamp] = {
                            'post_date': post_date,
                            'source_link': source_link
                        }

    return timestamp_data


def extract_timestamp_from_filename(filename):
    """从文件名中提取时间戳"""
    # 示例文件名: 20241224_102815_935857_gpt-4o_extract_cot.json
    parts = filename.split('_')
    if len(parts) >= 3:
        return '_'.join(parts[:3])  # 合并前三部分作为时间戳
    return None


def split_package_data(data_item, source, model, prompt_type, timestamp_info):
    """拆分包名和包管理器，返回拆分后的数据项列表"""
    # 如果是空对象，直接返回空列表
    if not data_item:
        return []

    results = []

    # 处理包名
    package_names = data_item.get('Package Name', [])
    if isinstance(package_names, str):
        package_names = [package_names]
    elif not package_names:
        package_names = ['unknown']

    # 获取包管理器，确保是列表
    package_managers = data_item.get('Package Manager', ['other'])
    if isinstance(package_managers, str):
        package_managers = [package_managers]
    elif not package_managers:
        package_managers = ['other']

    # 标准化包管理器名称
    package_managers = [normalize_package_manager(pm) for pm in package_managers]

    # 为每个包名和包管理器组合创建新的数据项
    for pkg_name in package_names:
        for pkg_manager in package_managers:
            new_item = deepcopy(data_item)
            new_item['Package Name'] = pkg_name
            new_item['Package Manager'] = pkg_manager

            # 添加源、模型和提示词类型信息
            new_item['Source'] = source
            new_item['Model'] = model
            new_item['Prompt'] = prompt_type

            # 添加时间戳相关信息
            new_item['file_timestamp'] = timestamp_info.get('timestamp', '')
            new_item['post_date'] = timestamp_info.get('post_date', '')
            new_item['source_link'] = timestamp_info.get('source_link', '')

            results.append(new_item)

    return results


def normalize_json_data(data):
    """标准化 JSON 数据格式"""
    if not data:
        return []

    if isinstance(data, dict):
        return [data]

    if isinstance(data, list):
        return [item for item in data if item]

    return []


def process_all_files(base_path, timestamp_data):
    """处理所有文件并返回合并的数据"""
    all_data = []
    processed_files = 0
    empty_files = 0
    error_files = []

    # 遍历所有子目录
    for source in os.listdir(base_path):
        source_path = os.path.join(base_path, source)
        if not os.path.isdir(source_path):
            continue

        # 遍历模型目录
        for model in os.listdir(source_path):
            model_path = os.path.join(source_path, model)
            if not os.path.isdir(model_path):
                continue

            # 遍历提示词类型目录
            for prompt_type in os.listdir(model_path):
                prompt_path = os.path.join(model_path, prompt_type)
                if not os.path.isdir(prompt_path):
                    continue

                # 处理JSON文件
                for file in os.listdir(prompt_path):
                    if not file.endswith('.json') or 'verify' not in file:
                        continue

                    # 从文件名提取时间戳
                    timestamp = extract_timestamp_from_filename(file)
                    timestamp_info = {
                        'timestamp': timestamp,
                        'post_date': '',
                        'source_link': ''
                    }
                    if timestamp and timestamp in timestamp_data:
                        timestamp_info.update(timestamp_data[timestamp])

                    file_path = os.path.join(prompt_path, file)
                    print(f"处理文件: {file_path}")

                    content = open(file_path, 'r', encoding='utf-8').read()
                    if not content.strip():
                        print(f"空文件: {file_path}")
                        empty_files += 1
                        continue

                    # 处理 Markdown 代码块格式
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]

                    content = content.strip()
                    if content in ['[]', '{}', '[{}]']:
                        print(f"空JSON文件: {file_path}")
                        empty_files += 1
                        continue

                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误 {file_path}: {str(e)}")
                        error_files.append((file_path, str(e)))
                        continue

                    # 标准化 JSON 数据
                    normalized_data = normalize_json_data(data)

                    if not normalized_data:
                        empty_files += 1
                        print(f"空内容文件: {file_path}")
                        continue

                    # 处理每个数据项
                    for item in normalized_data:
                        split_items = split_package_data(item, source, model, prompt_type, timestamp_info)
                        all_data.extend(split_items)

                    processed_files += 1

    print(f"\n处理完成:")
    print(f"- 处理文件数: {processed_files}")
    print(f"- 空文件数: {empty_files}")
    print(f"- 错误文件数: {len(error_files)}")
    print(f"- 总数据项数: {len(all_data)}")

    if error_files:
        print("\n错误文件列表:")
        for file_path, error in error_files:
            print(f"- {file_path}\n  错误: {error}")

    return all_data


def calculate_package_stats(data):
    """统计每种包管理器下的恶意包数量"""
    package_sets = defaultdict(set)

    for item in data:
        package_manager = item['Package Manager']
        package_name = item['Package Name']
        package_sets[package_manager].add(package_name)

    stats = {pm: len(packages) for pm, packages in package_sets.items()}
    sorted_stats = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    print("\n各包管理器恶意包统计:")
    print("-" * 30)
    for pm, count in sorted_stats.items():
        print(f"{pm}: {count} 个包")
    print("-" * 30)

    return sorted_stats


def main():
    # 基础路径
    base_path = '/Users/blue/Documents/Github/SCC_Intelligence/Dataset/NewJson'
    waiting_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/waiting_collection.txt'
    collected_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/collected_pagelinks.txt'

    # 加载时间戳映射数据
    timestamp_data = load_pagelinks_data(waiting_path, collected_path)

    # 处理所有文件
    all_data = process_all_files(base_path, timestamp_data)

    # 计算统计信息
    package_stats = calculate_package_stats(all_data)

    # 保存结果
    output_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/unstructured.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"- 结果保存于: {output_path}")


if __name__ == "__main__":
    main()