import json
import os
from typing import List, Set


def extract_source_links(json_data: dict) -> List[str]:
    """Extract source links from JSON data."""
    links = []

    if isinstance(json_data, dict):
        if 'source_link' in json_data:
            if isinstance(json_data['source_link'], list):
                links.extend(json_data['source_link'])
            elif isinstance(json_data['source_link'], str):
                links.append(json_data['source_link'])

        for value in json_data.values():
            links.extend(extract_source_links(value))

    elif isinstance(json_data, list):
        for item in json_data:
            links.extend(extract_source_links(item))

    return links


def process_json_file(file_path: str) -> Set[str]:
    """Process a single JSON file and return a set of deduplicated source_link."""
    try:
        print(f"Processing file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        links = extract_source_links(data)
        unique_links = set(links)
        print(f"Found {len(links)} source_link, {len(unique_links)} after deduplication")
        return unique_links
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return set()


def main():
    json_file = "./name_formated.json"

    if len(os.sys.argv) > 1:
        json_file = os.sys.argv[1]

    all_source_links = process_json_file(json_file)

    print(f"\nTotal number of deduplicated source_link: {len(all_source_links)}")

    if len(all_source_links) <= 100 or input("Do you want to display all links? (y/n): ").lower() == 'y':
        print("\nAll deduplicated source_link:")
        for link in sorted(all_source_links):
            print(f"- {link}")


if __name__ == "__main__":
    main()
