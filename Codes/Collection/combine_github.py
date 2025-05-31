# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : merge_github_data
# @Project  : SCC_Intelligence
# Time      : 1/6/25 
# Author    : blue
# version   : python 
# Description：合并 github.json 数据到 formated_packages.json
"""

# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : merge_github_data
# @Project  : SCC_Intelligence
# Time      : 1/6/25 
# Author    : blue
# version   : python 
# Description：合并 github.json 数据到 formated_packages.json
"""

import json
import os
from copy import deepcopy
from datetime import datetime


def format_date(date_str):
    """格式化日期字符串为 YYYY-MM-DD 格式"""
    if not date_str:
        return ''

    try:
        # 处理带有时区的ISO格式日期
        if isinstance(date_str, str) and 'T' in date_str:
            dt = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        # 如果已经是YYYY-MM-DD格式
        elif isinstance(date_str, str) and len(date_str.split('-')) == 3:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        return str(date_str)
    except Exception as e:
        print(f"日期格式化错误: {date_str} - {str(e)}")
        return str(date_str)


def load_pagelinks_data(waiting_path, collected_path):
    """加载pagelinks数据，返回时间戳到post_date和source_link的映射"""
    timestamp_data = {}
    duplicate_count = 0

    for file_path in [waiting_path, collected_path]:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        timestamp = parts[0].strip()
                        post_date = parts[2].strip()
                        source_link = parts[3].strip()

                        # 格式化日期
                        formatted_date = format_date(post_date)

                        timestamp_data[timestamp] = {
                            'post_date': formatted_date,
                            'source_link': source_link
                        }

    return timestamp_data


def convert_github_data(github_data, timestamp_data):
    """转换 github 数据到目标格式，包含新增字段"""
    converted_data = []

    for package in github_data.get('packages', []):
        # 创建新的数据项
        new_item = {
            "Package Name": package.get('package_name', ''),
            "Package Manager": package.get('package_manager', 'other'),
            "Source": "github",
            "Model": "github",
            "Prompt": "default",
            "file_timestamp": package.get('timestamp', ''),
            "Version": package.get('affected_version', ''),
            "Date of Discovery": format_date(package.get('update_date', '')),
            "Method of Attack": package.get('overview', '')
        }

        # 查找对应的时间戳数据
        timestamp = package.get('timestamp', '')
        update_date = package.get('update_date', '')

        if timestamp in timestamp_data:
            new_item['post_date'] = timestamp_data[timestamp]['post_date']
            new_item['source_link'] = timestamp_data[timestamp]['source_link']
        else:
            # 如果在映射数据中找不到，使用 update_date 作为 post_date
            new_item['post_date'] = format_date(update_date)
            new_item['source_link'] = ''

        converted_data.append(new_item)

    return converted_data


def merge_data(github_path, formated_path, waiting_path, collected_path, output_path):
    """合并数据并保存"""
    # 加载时间戳映射数据
    timestamp_data = load_pagelinks_data(waiting_path, collected_path)

    # 加载 github 数据
    with open(github_path, 'r', encoding='utf-8') as f:
        github_data = json.load(f)

    # 转换 github 数据
    github_converted = convert_github_data(github_data, timestamp_data)

    # 加载现有的 formated 数据
    with open(formated_path, 'r', encoding='utf-8') as f:
        formated_data = json.load(f)

    # 格式化现有数据中的日期
    for item in formated_data:
        if 'post_date' in item:
            try:
                item['post_date'] = format_date(item['post_date'])
            except Exception:
                # 如果格式化失败且有 Date of Discovery，使用它
                if 'Date of Discovery' in item:
                    item['post_date'] = format_date(item['Date of Discovery'])

        if 'Date of Discovery' in item:
            item['Date of Discovery'] = format_date(item['Date of Discovery'])

        # 移除现有数据中的 affected_version 字段
        if 'affected_version' in item:
            del item['affected_version']

    # 合并数据
    merged_data = formated_data + github_converted

    # 保存合并后的数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"\n数据合并完成:")
    print(f"- Github数据项数: {len(github_converted)}")
    print(f"- 原格式化数据项数: {len(formated_data)}")
    print(f"- 合并后总数据项数: {len(merged_data)}")
    print(f"- 结果保存于: {output_path}")


def main():
    # 定义路径
    github_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/github.json'
    formated_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/formated_packages.json'
    waiting_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/waiting_collection.txt'
    collected_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/collected_pagelinks.txt'
    output_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/formated_packages1.json'

    # 执行合并
    merge_data(github_path, formated_path, waiting_path, collected_path, output_path)


if __name__ == "__main__":
    main()