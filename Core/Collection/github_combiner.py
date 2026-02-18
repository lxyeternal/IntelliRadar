import json
import os
from copy import deepcopy
from datetime import datetime


def format_date(date_str):
    """Format date string to YYYY-MM-DD format."""
    if not date_str:
        return ''

    try:
        if isinstance(date_str, str) and 'T' in date_str:
            dt = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        elif isinstance(date_str, str) and len(date_str.split('-')) == 3:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        return str(date_str)
    except Exception as e:
        print(f"Date formatting error: {date_str} - {str(e)}")
        return str(date_str)


def load_pagelinks_data(waiting_path, collected_path):
    """Load pagelinks data, return timestamp to post_date and source_link mapping."""
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

                        formatted_date = format_date(post_date)

                        timestamp_data[timestamp] = {
                            'post_date': formatted_date,
                            'source_link': source_link
                        }

    return timestamp_data


def convert_github_data(github_data, timestamp_data):
    """Convert github data to target format, including new fields."""
    converted_data = []

    for package in github_data.get('packages', []):
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

        timestamp = package.get('timestamp', '')
        update_date = package.get('update_date', '')

        if timestamp in timestamp_data:
            new_item['post_date'] = timestamp_data[timestamp]['post_date']
            new_item['source_link'] = timestamp_data[timestamp]['source_link']
        else:
            new_item['post_date'] = format_date(update_date)
            new_item['source_link'] = ''

        converted_data.append(new_item)

    return converted_data


def merge_data(github_path, formated_path, waiting_path, collected_path, output_path):
    timestamp_data = load_pagelinks_data(waiting_path, collected_path)

    with open(github_path, 'r', encoding='utf-8') as f:
        github_data = json.load(f)

    github_converted = convert_github_data(github_data, timestamp_data)

    with open(formated_path, 'r', encoding='utf-8') as f:
        formated_data = json.load(f)

    for item in formated_data:
        if 'post_date' in item:
            try:
                item['post_date'] = format_date(item['post_date'])
            except Exception:
                if 'Date of Discovery' in item:
                    item['post_date'] = format_date(item['Date of Discovery'])

        if 'Date of Discovery' in item:
            item['Date of Discovery'] = format_date(item['Date of Discovery'])

        if 'affected_version' in item:
            del item['affected_version']

    merged_data = formated_data + github_converted

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"\nData merged successfully:")
    print(f"- Github data items: {len(github_converted)}")
    print(f"- Original formatted data items: {len(formated_data)}")
    print(f"- Merged total data items: {len(merged_data)}")
    print(f"- Result saved in: {output_path}")


def main():
    github_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/github.json'
    formated_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/formated_packages.json'
    waiting_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/waiting_collection.txt'
    collected_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/pagelinks/collected_pagelinks.txt'
    output_path = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/formated_packages1.json'

    merge_data(github_path, formated_path, waiting_path, collected_path, output_path)


if __name__ == "__main__":
    main()
