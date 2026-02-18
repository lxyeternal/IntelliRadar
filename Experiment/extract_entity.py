#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import os
import csv
from typing import Dict, List, Union, Set
from collections import defaultdict


def normalize_package_manager(manager: Union[str, List[str]]) -> str:
    """Normalize package manager name"""
    if not manager or (isinstance(manager, list) and (not manager or manager[0] in ["", None])):
        return "other"
    if isinstance(manager, list):
        manager = manager[0]
    manager = manager.lower() if manager else "other"
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


def get_version_key(item: dict) -> str:
    """Get the version key from item"""
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
    """
    Check whether JSON content is empty.

    Checks for: [{}], empty dict {}, array containing empty dict [{}],
    and nested structures containing any of the above.
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
        if not content:
            return True
        return any(is_empty_json(v) for v in content.values())

    elif isinstance(content, list):
        if not content:
            return True
        if content == [{}]:
            return True
        return all(is_empty_json(item) for item in content)

    return False


def process_json_file(file_path: str, source: str, file_name: str) -> List[dict]:
    """Process a single JSON file and return package info list"""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if is_empty_json(content):
            return results

        try:
            parsed_json = json.loads(content)

        except json.JSONDecodeError as e:
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                try:
                    parsed_json = json.loads(json_str)
                    if is_empty_json(parsed_json):
                        return results
                except json.JSONDecodeError as e:
                    print(f"\nJSON parse error - file: {file_path}")
                    print(f"Error: {str(e)}")
                    return results
            else:
                print(f"\nNo valid JSON content found - file: {file_path}")
                return results

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
                package_name_key = get_package_name_key(item)
                package_names = item[package_name_key]
                if isinstance(package_names, str):
                    package_names = [package_names]

                manager_key = get_package_manager_key(item)
                package_manager = item.get(manager_key, 'other') if manager_key else 'other'
                manager = normalize_package_manager(package_manager)

                version_key = get_version_key(item)
                version = item.get(version_key, '') if version_key else ''
                if isinstance(version, list):
                    version = version[0] if version else ''

                for pkg_name in package_names:
                    if pkg_name:
                        results.append({
                            'package': pkg_name.lower(),
                            'version': str(version),
                            'package_manager': manager,
                            'source': source,
                            'file_name': file_name
                        })

            except KeyError as e:
                print(f"\nMissing field - file: {file_path}")
                print(f"Missing: {str(e)}")
                continue

    except Exception as e:
        print(f"\nError processing file: {file_path}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error: {str(e)}")
        return results

    return results


def process_directory(base_path: str, output_file: str):
    """Process directory and generate CSV file"""
    all_records = []
    processed_files = 0
    processed_dirs = 0

    print(f"\nStarting to process base directory: {base_path}")
    if not os.path.exists(base_path):
        print(f"Error: base directory does not exist: {base_path}")
        return

    newjson_path = os.path.join(base_path, "NewJson")
    if not os.path.exists(newjson_path):
        print(f"Error: NewJson directory does not exist: {newjson_path}")
        return

    try:
        sources = [d for d in os.listdir(newjson_path) if os.path.isdir(os.path.join(newjson_path, d))]
        print(f"Found source directories: {sources}")
    except Exception as e:
        print(f"Error reading directory: {str(e)}")
        return

    if not sources:
        print("No source directories found")
        return

    sources = ["medium"]
    for source in sources:
        source_path = os.path.join(newjson_path, source)
        cot_path = os.path.join(source_path, 'gpt-4o', 'cot')

        print(f"\nChecking directory: {source}")
        print(f"Looking for cot path: {cot_path}")

        if os.path.exists(cot_path) and os.path.isdir(cot_path):
            processed_dirs += 1
            print(f"Processing directory: {source}/gpt-4o/cot")

            json_files = [f for f in os.listdir(cot_path)
                          if f.endswith('.json') and '_verify_' in f]
            print(f"Found {len(json_files)} matching JSON files")

            for file_name in json_files:
                file_path = os.path.join(cot_path, file_name)

                records = process_json_file(file_path, source, file_name)

                all_records.extend(records)
                processed_files += 1

                if processed_files % 10 == 0:
                    print(f"Processed {processed_files} files...")
        else:
            print(f"cot directory not found: {cot_path}")

    if all_records:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['package', 'version', 'package_manager', 'source', 'file_name'])
            writer.writeheader()
            writer.writerows(all_records)

    print(f"\nProcessing complete!")
    print(f"Total directories processed: {processed_dirs}")
    print(f"Total files processed: {processed_files}")
    print(f"Total records extracted: {len(all_records)}")
    print(f"Data saved to: {output_file}")

    if not all_records:
        print("\nWarning: no data extracted, please check:")
        print("1. Directory structure (NewJson/source/gpt-4o/cot/...)")
        print("2. Filenames contain '_relation_'")
        print("3. JSON file format is correct")
        print("4. Read permissions are available")


def main():
    base_path = '/Users/blue/Documents/Github/SCC_Intelligence/Dataset'
    output_file = 'package_data_4o.csv'
    process_directory(base_path, output_file)


if __name__ == "__main__":
    main()
