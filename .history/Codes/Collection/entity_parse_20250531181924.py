

import os
import json
from collections import defaultdict, Counter
from copy import deepcopy


def normalize_package_manager(pkg_manager):
    if not pkg_manager or pkg_manager.lower() in ['unknown', 'n/a']:
        return 'other'

    pkg_manager = pkg_manager.lower()
    if pkg_manager in ['pypi', 'python', 'pip']:
        return 'pypi'
    return pkg_manager


def load_pagelinks_data(waiting_path, collected_path):
    timestamp_data = {}

    for file_path in [waiting_path, collected_path]:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:  
                        timestamp = parts[0].strip()
                        post_date = parts[2].strip()
                        source_link = parts[3].strip()
                        timestamp_data[timestamp] = {
                            'post_date': post_date,
                            'source_link': source_link
                        }

    return timestamp_data


def extract_timestamp_from_filename(filename):
    parts = filename.split('_')
    if len(parts) >= 3:
        return '_'.join(parts[:3])  
    return None


def split_package_data(data_item, source, model, prompt_type, timestamp_info):
    if not data_item:
        return []

    results = []

    package_names = data_item.get('Package Name', [])
    if isinstance(package_names, str):
        package_names = [package_names]
    elif not package_names:
        package_names = ['unknown']

    package_managers = data_item.get('Package Manager', ['other'])
    if isinstance(package_managers, str):
        package_managers = [package_managers]
    elif not package_managers:
        package_managers = ['other']

    package_managers = [normalize_package_manager(pm) for pm in package_managers]

    for pkg_name in package_names:
        for pkg_manager in package_managers:
            new_item = deepcopy(data_item)
            new_item['Package Name'] = pkg_name
            new_item['Package Manager'] = pkg_manager

            new_item['Source'] = source
            new_item['Model'] = model
            new_item['Prompt'] = prompt_type

            new_item['file_timestamp'] = timestamp_info.get('timestamp', '')
            new_item['post_date'] = timestamp_info.get('post_date', '')
            new_item['source_link'] = timestamp_info.get('source_link', '')

            results.append(new_item)

    return results


def normalize_json_data(data):
    if not data:
        return []

    if isinstance(data, dict):
        return [data]

    if isinstance(data, list):
        return [item for item in data if item]

    return []


def process_all_files(base_path, timestamp_data):
    all_data = []
    processed_files = 0
    empty_files = 0
    error_files = []

    for source in os.listdir(base_path):
        source_path = os.path.join(base_path, source)
        if not os.path.isdir(source_path):
            continue

        for model in os.listdir(source_path):
            model_path = os.path.join(source_path, model)
            if not os.path.isdir(model_path):
                continue

            for prompt_type in os.listdir(model_path):
                prompt_path = os.path.join(model_path, prompt_type)
                if not os.path.isdir(prompt_path):
                    continue

                for file in os.listdir(prompt_path):
                    if not file.endswith('.json') or 'verify' not in file:
                        continue

                    timestamp = extract_timestamp_from_filename(file)
                    timestamp_info = {
                        'timestamp': timestamp,
                        'post_date': '',
                        'source_link': ''
                    }
                    if timestamp and timestamp in timestamp_data:
                        timestamp_info.update(timestamp_data[timestamp])

                    file_path = os.path.join(prompt_path, file)
                    print(f"Processing file: {file_path}")

                    content = open(file_path, 'r', encoding='utf-8').read()
                    if not content.strip():
                        print(f"Empty file: {file_path}")
                        empty_files += 1
                        continue

                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]

                    content = content.strip()
                    if content in ['[]', '{}', '[{}]']:
                        print(f"Empty JSON file: {file_path}")
                        empty_files += 1
                        continue

                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error {file_path}: {str(e)}")
                        error_files.append((file_path, str(e)))
                        continue

                    normalized_data = normalize_json_data(data)

                    if not normalized_data:
                        empty_files += 1
                        print(f"Empty content file: {file_path}")
                        continue

                    for item in normalized_data:
                        split_items = split_package_data(item, source, model, prompt_type, timestamp_info)
                        all_data.extend(split_items)

                    processed_files += 1

    print(f"\nProcessing completed:")
    print(f"- Processed files: {processed_files}")
    print(f"- Empty files: {empty_files}")
    print(f"- Error files: {len(error_files)}")
    print(f"- Total data items: {len(all_data)}")

    if error_files:
        print("\nError files list:")
        for file_path, error in error_files:
            print(f"- {file_path}\n   Error: {error}")

    return all_data


def calculate_package_stats(data):
    package_sets = defaultdict(set)

    for item in data:
        package_manager = item['Package Manager']
        package_name = item['Package Name']
        package_sets[package_manager].add(package_name)

    stats = {pm: len(packages) for pm, packages in package_sets.items()}
    sorted_stats = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    print("\nPackage manager malicious package statistics:")
    print("-" * 30)
    for pm, count in sorted_stats.items():
        print(f"{pm}: {count} packages")
    print("-" * 30)

    return sorted_stats


def main():
    base_path = '/Users/blue/Documents/Github/SCC_Intelligence/Dataset/NewJson'
    waiting_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/waiting_collection.txt'
    collected_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/collected_pagelinks.txt'

    timestamp_data = load_pagelinks_data(waiting_path, collected_path)

    all_data = process_all_files(base_path, timestamp_data)

    package_stats = calculate_package_stats(all_data)

    output_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/unstructured.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"- Result saved in: {output_path}")


if __name__ == "__main__":
    main()