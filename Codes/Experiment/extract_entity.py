# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : extract_entity
# @Project  : SCC_Intelligence
# Time      : 1/3/25 19:32
# Author    : blue
# version   : python 
# Description：
"""

import json
import os
import csv
from typing import Dict, List, Union, Set
from collections import defaultdict


def normalize_package_manager(manager: Union[str, List[str]]) -> str:
    """标准化包管理器名称"""
    if not manager or (isinstance(manager, list) and (not manager or manager[0] in ["", None])):
        return "other"
    if isinstance(manager, list):
        manager = manager[0]
    manager = manager.lower() if manager else "other"
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


def get_version_key(item: dict) -> str:
    """获取版本号的键"""
    possible_keys = [
        'Version', 'version', 'VERSION',
        'Package Version', 'package version', 'PackageVersion',
        'package_version', 'Package_Version', 'PACKAGE_VERSION'
    ]
    for key in possible_keys:
        if key in item:
            return key
    return None


def is_empty_json(content: Union[str, dict, list]) -> bool:
    """检查JSON内容是否为空

    检查以下情况：
    1. 字符串中包含 [{}]
    2. 空对象 {}
    3. 包含空对象的数组 [{}]
    4. 嵌套结构中包含上述任意情况
    """
    if isinstance(content, str):
        if '[{}]' in content:
            return True
        try:
            parsed = json.loads(content)
            return is_empty_json(parsed)
        except json.JSONDecodeError:
            return False

    elif isinstance(content, dict):
        if not content:  # 空字典 {}
            return True
        # 检查字典的每个值
        return any(is_empty_json(v) for v in content.values())

    elif isinstance(content, list):
        if not content:  # 空列表 []
            return True
        if content == [{}]:  # [{}] 情况
            return True
        # 检查列表的每个元素
        return all(is_empty_json(item) for item in content)

    return False


def process_json_file(file_path: str, source: str, file_name: str) -> List[dict]:
    """处理单个JSON文件并返回包信息列表"""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # 检查是否为空JSON
        if is_empty_json(content):
            return results

        try:
            parsed_json = json.loads(content)

        except json.JSONDecodeError as e:
            # 尝试从内容中提取JSON
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                try:
                    parsed_json = json.loads(json_str)
                    # 再次检查提取的JSON是否为空
                    if is_empty_json(parsed_json):
                        return results
                except json.JSONDecodeError as e:
                    print(f"\nJSON解析错误 - 文件路径: {file_path}")
                    print(f"错误信息: {str(e)}")
                    return results
            else:
                print(f"\n无法找到有效的JSON内容 - 文件路径: {file_path}")
                return results

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
            return results

        for item in data:
            try:
                # 获取包名
                package_name_key = get_package_name_key(item)
                package_names = item[package_name_key]
                if isinstance(package_names, str):
                    package_names = [package_names]

                # 获取包管理器
                manager_key = get_package_manager_key(item)
                package_manager = item.get(manager_key, 'other') if manager_key else 'other'
                manager = normalize_package_manager(package_manager)

                # 获取版本号
                version_key = get_version_key(item)
                version = item.get(version_key, '') if version_key else ''
                if isinstance(version, list):
                    version = version[0] if version else ''

                # 为每个包名创建一条记录
                for pkg_name in package_names:
                    if pkg_name:  # 确保包名不为空
                        results.append({
                            'package': pkg_name.lower(),
                            'version': str(version),
                            'package_manager': manager,
                            'source': source,
                            'file_name': file_name
                        })

            except KeyError as e:
                print(f"\n字段缺失 - 文件路径: {file_path}")
                print(f"缺失字段: {str(e)}")
                continue

    except Exception as e:
        print(f"\n处理文件时发生错误 - 文件路径: {file_path}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        return results

    return results


def process_directory(base_path: str, output_file: str):
    """处理目录并生成CSV文件"""
    all_records = []
    processed_files = 0
    processed_dirs = 0

    print(f"\n开始处理基础目录: {base_path}")
    if not os.path.exists(base_path):
        print(f"错误: 基础目录不存在: {base_path}")
        return

    # 首先获取NewJson目录
    newjson_path = os.path.join(base_path, "NewJson")
    if not os.path.exists(newjson_path):
        print(f"错误: NewJson目录不存在: {newjson_path}")
        return

    # 获取所有source目录（如bleepingcomputer等）
    try:
        sources = [d for d in os.listdir(newjson_path) if os.path.isdir(os.path.join(newjson_path, d))]
        print(f"找到的source目录: {sources}")
    except Exception as e:
        print(f"读取目录出错: {str(e)}")
        return

    if not sources:
        print("未找到任何source目录")
        return

    sources = ["medium"]
    for source in sources:
        source_path = os.path.join(newjson_path, source)
        # 在source目录下寻找gpt-4o/cot路径
        cot_path = os.path.join(source_path, 'gpt-4o', 'cot')
        # cot_path = os.path.join(source_path, 'csl-malicious-4o-mini', 'default')

        print(f"\n检查目录: {source}")
        print(f"查找cot路径: {cot_path}")

        if os.path.exists(cot_path) and os.path.isdir(cot_path):
            processed_dirs += 1
            print(f"处理目录: {source}/gpt-4o/cot")

            # 获取所有JSON文件
            json_files = [f for f in os.listdir(cot_path)
                          if f.endswith('.json') and '_verify_' in f]
            print(f"找到{len(json_files)}个符合条件的JSON文件")

            # 处理目录中的所有JSON文件
            for file_name in json_files:
                file_path = os.path.join(cot_path, file_name)

                # 将文件名传入process_json_file，source就是bleepingcomputer这一级的目录名
                records = process_json_file(file_path, source, file_name)

                all_records.extend(records)
                processed_files += 1

                if processed_files % 10 == 0:  # 每处理10个文件打印一次进度
                    print(f"已处理 {processed_files} 个文件...")
        else:
            print(f"未找到cot目录: {cot_path}")

    # 写入CSV文件
    if all_records:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['package', 'version', 'package_manager', 'source', 'file_name'])
            writer.writeheader()
            writer.writerows(all_records)

    # 打印统计信息
    print(f"\n处理完成!")
    print(f"总共处理了 {processed_dirs} 个目录")
    print(f"总共处理了 {processed_files} 个文件")
    print(f"总共提取了 {len(all_records)} 条记录")
    print(f"数据已保存到: {output_file}")

    if not all_records:
        print("\n警告: 未提取到任何数据，请检查:")
        print("1. 目录结构是否正确 (NewJson/source/gpt-4o/cot/...)")
        print("2. 文件名是否包含'_relation_'")
        print("3. JSON文件格式是否正确")
        print("4. 是否有读取权限")

    # 写入CSV文件
    if all_records:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['package', 'version', 'package_manager', 'source', 'file_name'])
            writer.writeheader()
            writer.writerows(all_records)

    # 打印统计信息
    print(f"\n处理完成!")
    print(f"总共处理了 {processed_dirs} 个目录")
    print(f"总共处理了 {processed_files} 个文件")
    print(f"总共提取了 {len(all_records)} 条记录")
    print(f"数据已保存到: {output_file}")


def main():
    base_path = '/Users/blue/Documents/Github/SCC_Intelligence/Dataset'
    output_file = 'package_data_4o.csv'
    process_directory(base_path, output_file)


if __name__ == "__main__":
    main()