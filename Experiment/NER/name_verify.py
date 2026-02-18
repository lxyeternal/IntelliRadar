#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Per-file package name verification: for each groundtruth file, check whether
the corresponding CTIKG and SecBERT files contain the same package names.
"""

import os
import json
import re
from collections import defaultdict


def extract_package_names_from_file(file_path):
    """Extract package names from a single groundtruth file"""
    packages = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

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
                return packages

            for item in data:
                package_names = None
                for key in ['Package Name', 'package name', 'PackageName', 'packagename',
                           'package_name', 'Package_Name', 'PACKAGE_NAME', 'PACKAGENAME',
                           'Package Names', 'package names', 'PackageNames', 'packagenames',
                           'package_names', 'Package_Names', 'PACKAGE_NAMES', 'PACKAGENAMES']:
                    if key in item:
                        package_names = item[key]
                        break

                if package_names:
                    if isinstance(package_names, str):
                        names = [package_names.lower()]
                    else:
                        names = [name.lower() for name in package_names]

                    for name in names:
                        packages.add(name)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in {file_path}: {e}")
            return packages

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return packages

    return packages


def extract_all_ctikg_packages(file_path):
    """Extract all package names from a CTIKG file using precise patterns"""
    all_packages = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            triples = data.get('extracted_triples', '')

        package_patterns = [
            r'\[SUBJECT:([^,\]]+), RELATION:is, OBJECT:malicious (?:npm|pypi|python) package\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:is|contains), OBJECT:malicious (?:npm|pypi|python) package\]',
            r'\[SUBJECT:malicious (?:npm|pypi|python) package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
            r'\[SUBJECT:malicious package, RELATION:masquerades, OBJECT:([^,\]]+)\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:designed to|steals|contains), OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:published|hosted|available), OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:(?:claimed to provide|downloaded), OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:version, OBJECT:[^,\]]+\]',
            r'\[SUBJECT:([^,\]]+), RELATION:published, OBJECT:[^,\]]+\]',
            r'masquerades, OBJECT:([^,\]]+)',
            r'\[SUBJECT:([a-zA-Z0-9_-]+), RELATION:(?:is|contains|steals), OBJECT:(?:malicious|sensitive)',
        ]

        for pattern in package_patterns:
            matches = re.findall(pattern, triples)
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if group and group.strip():
                            all_packages.add(group.strip().lower())
                elif match and match.strip():
                    all_packages.add(match.strip().lower())

        # Fallback: use broader extraction if no packages found
        if not all_packages:
            pattern = r'SUBJECT:([^,]+)'
            subjects = re.findall(pattern, triples)
            for subject in subjects:
                entity = subject.strip().lower()
                if entity and len(entity) > 1 and not entity.startswith('the '):
                    all_packages.add(entity)

            pattern = r'OBJECT:([^,\]]+)'
            objects = re.findall(pattern, triples)
            for obj in objects:
                entity = obj.strip().lower()
                if entity and len(entity) > 1 and not entity.startswith('the '):
                    all_packages.add(entity)

        non_packages = {'the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they', 'them',
                       'malicious', 'vulnerable', 'package', 'packages', 'module', 'modules',
                       'library', 'libraries', 'dependency', 'dependencies', 'code', 'software'}
        all_packages = {pkg for pkg in all_packages if pkg not in non_packages and len(pkg) > 1}

    except Exception as e:
        print(f"Error extracting packages from CTIKG file {file_path}: {e}")

    return all_packages


def check_packages_in_ctikg_file(packages, file_path):
    """Check whether package names exist in a CTIKG file"""
    found_packages = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        for package in packages:
            pattern = r'\[SUBJECT:' + re.escape(package) + r'[,\]]|\[SUBJECT:[^,]+, RELATION:[^,]+, OBJECT:' + re.escape(package) + r'[,\]]'
            if re.search(pattern, content, re.IGNORECASE):
                found_packages.add(package)
                continue

            pattern = r'SUBJECT:([^,]+)'
            subjects = re.findall(pattern, content)
            for subject in subjects:
                if subject.strip().lower() == package:
                    found_packages.add(package)
                    break

            pattern = r'OBJECT:([^,\]]+)'
            objects = re.findall(pattern, content)
            for obj in objects:
                if obj.strip().lower() == package:
                    found_packages.add(package)
                    break

    except Exception as e:
        print(f"Error checking CTIKG file {file_path}: {e}")

    return found_packages


def check_packages_in_secbert_file(packages, file_path):
    """Check whether package names exist in SecBERT entity list"""
    found_packages = set()
    label1_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        entities = data.get('entities', [])

        for entity in entities:
            if entity.get('type') == 'LABEL_1':
                label1_count += 1

        for package in packages:
            for entity in entities:
                entity_text = entity.get('entity', '').strip().lower()
                if entity_text == package.lower():
                    found_packages.add(package)
                    break

    except Exception as e:
        print(f"Error checking SecBERT file {file_path}: {e}")

    return found_packages, label1_count


def main():
    groundtruth_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/groundtruth'
    ctikg_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/CTIKG/extracted_packages'
    secbert_dir = '/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/major/NER/SecBERT/SecBERT_entity'

    groundtruth_files = [f for f in os.listdir(groundtruth_dir) if f.endswith('.json')]
    print(f"Found {len(groundtruth_files)} groundtruth files")

    results = {
        'total_files': len(groundtruth_files),
        'total_packages': 0,
        'ctikg': {'found': 0, 'not_found': 0, 'file_details': {}, 'all_packages': set()},
        'secbert': {'found': 0, 'not_found': 0, 'file_details': {}, 'total_label1_entities': 0}
    }

    all_packages = set()
    all_found_ctikg = set()
    all_found_secbert = set()

    for i, filename in enumerate(groundtruth_files, 1):
        print(f"Processing file {i}/{len(groundtruth_files)}: {filename}")

        groundtruth_file = os.path.join(groundtruth_dir, filename)
        ctikg_file = os.path.join(ctikg_dir, filename)
        secbert_file = os.path.join(secbert_dir, filename)

        groundtruth_packages = extract_package_names_from_file(groundtruth_file)

        if not groundtruth_packages:
            print(f"  - Warning: no package names found in {filename}")
            continue

        results['total_packages'] += len(groundtruth_packages)
        all_packages.update(groundtruth_packages)

        ctikg_found_packages = set()
        ctikg_all_packages = set()
        if os.path.exists(ctikg_file):
            ctikg_found_packages = check_packages_in_ctikg_file(groundtruth_packages, ctikg_file)
            ctikg_all_packages = extract_all_ctikg_packages(ctikg_file)
            results['ctikg']['found'] += len(ctikg_found_packages)
            results['ctikg']['not_found'] += len(groundtruth_packages) - len(ctikg_found_packages)
            results['ctikg']['all_packages'].update(ctikg_all_packages)
            all_found_ctikg.update(ctikg_found_packages)
        else:
            print(f"  - Warning: corresponding CTIKG file not found: {filename}")
            results['ctikg']['not_found'] += len(groundtruth_packages)

        secbert_found_packages = set()
        file_label1_count = 0
        if os.path.exists(secbert_file):
            secbert_found_packages, file_label1_count = check_packages_in_secbert_file(groundtruth_packages, secbert_file)
            results['secbert']['found'] += len(secbert_found_packages)
            results['secbert']['not_found'] += len(groundtruth_packages) - len(secbert_found_packages)
            results['secbert']['total_label1_entities'] += file_label1_count
            all_found_secbert.update(secbert_found_packages)
        else:
            print(f"  - Warning: corresponding SecBERT file not found: {filename}")
            results['secbert']['not_found'] += len(groundtruth_packages)

        results['ctikg']['file_details'][filename] = {
            'total': len(groundtruth_packages),
            'found': len(ctikg_found_packages),
            'not_found': len(groundtruth_packages) - len(ctikg_found_packages),
            'found_packages': sorted(list(ctikg_found_packages)),
            'not_found_packages': sorted(list(groundtruth_packages - ctikg_found_packages)),
            'all_packages': len(ctikg_all_packages)
        }

        results['secbert']['file_details'][filename] = {
            'total': len(groundtruth_packages),
            'found': len(secbert_found_packages),
            'not_found': len(groundtruth_packages) - len(secbert_found_packages),
            'label1_count': file_label1_count,
            'found_packages': sorted(list(secbert_found_packages)),
            'not_found_packages': sorted(list(groundtruth_packages - secbert_found_packages))
        }

        print(f"  - Groundtruth package count: {len(groundtruth_packages)}")
        print(f"  - CTIKG found: {len(ctikg_found_packages)}/{len(groundtruth_packages)} ({len(ctikg_found_packages)/len(groundtruth_packages)*100:.1f}%)")
        print(f"  - CTIKG total identified packages: {len(ctikg_all_packages)}")
        print(f"  - SecBERT found: {len(secbert_found_packages)}/{len(groundtruth_packages)} ({len(secbert_found_packages)/len(groundtruth_packages)*100:.1f}%)")
        print(f"  - SecBERT LABEL_1 entity count: {file_label1_count}")

    # Fixed groundtruth total (deduplicated)
    unique_total = 675
    unique_ctikg_found = len(all_found_ctikg)
    unique_secbert_found = len(all_found_secbert)
    total_ctikg_packages = len(results['ctikg']['all_packages'])

    if total_ctikg_packages < unique_ctikg_found:
        print(f"Warning: CTIKG total identified ({total_ctikg_packages}) < correctly identified ({unique_ctikg_found}), adjusting to equal")
        total_ctikg_packages = unique_ctikg_found

    ctikg_tp = unique_ctikg_found
    ctikg_fn = unique_total - unique_ctikg_found
    ctikg_fp = total_ctikg_packages - unique_ctikg_found

    ctikg_precision = ctikg_tp / total_ctikg_packages if total_ctikg_packages > 0 else 0
    ctikg_recall = ctikg_tp / unique_total if unique_total > 0 else 0
    ctikg_f1 = 2 * ctikg_precision * ctikg_recall / (ctikg_precision + ctikg_recall) if (ctikg_precision + ctikg_recall) > 0 else 0

    secbert_tp = unique_secbert_found
    secbert_fn = unique_total - unique_secbert_found
    secbert_fp = results['secbert']['total_label1_entities'] - unique_secbert_found

    secbert_precision = secbert_tp / results['secbert']['total_label1_entities'] if results['secbert']['total_label1_entities'] > 0 else 0
    secbert_recall = secbert_tp / unique_total if unique_total > 0 else 0
    secbert_f1 = 2 * secbert_precision * secbert_recall / (secbert_precision + secbert_recall) if (secbert_precision + secbert_recall) > 0 else 0

    print("\n" + "="*50)
    print("Tool Evaluation Results")
    print("="*50)

    print(f"\nGroundtruth total package names (deduplicated): {unique_total}")

    print("\n=== CTIKG Tool ===")
    print(f"Total identified package names: {total_ctikg_packages}")
    print(f"Correctly identified (TP): {ctikg_tp}")
    print(f"Incorrectly identified (FP): {ctikg_fp}")
    print(f"Not identified (FN): {ctikg_fn}")
    print(f"Precision: {ctikg_precision:.4f}")
    print(f"Recall: {ctikg_recall:.4f}")
    print(f"F1 Score: {ctikg_f1:.4f}")

    print("\n=== SecBERT Tool ===")
    print(f"Total identified entities (LABEL_1): {results['secbert']['total_label1_entities']}")
    print(f"Correctly identified (TP): {secbert_tp}")
    print(f"Incorrectly identified (FP): {secbert_fp}")
    print(f"Not identified (FN): {secbert_fn}")
    print(f"Precision: {secbert_precision:.4f}")
    print(f"Recall: {secbert_recall:.4f}")
    print(f"F1 Score: {secbert_f1:.4f}")


if __name__ == "__main__":
    main()
