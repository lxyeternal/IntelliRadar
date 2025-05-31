# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : aggcount
# @Project  : SCC_Intelligence
# Time      : 1/9/25 14:31
# version   : python 
# Description：
"""

import json
from collections import defaultdict
from typing import Dict, List, Set


def analyze_entities(file_path: str) -> Dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    TOTAL_PACKAGES = 34313  # Total number of packages

    entity_fields = [
        "Package Name",
        "Package Manager",
        "Version",
        "Date of Discovery",
        "Repository URL",
        "Method of Attack",
        "Discoverer",
        "Impacted Systems",
        "Attack Vector",
        "Indicators of Compromise"
    ]

    # Group data by package name
    package_groups = defaultdict(list)
    for item in data:
        package_groups[item["Package Name"]].append(item)

    results = {
        "total_packages": len(package_groups),
        "total_all_packages": TOTAL_PACKAGES,
        "multi_source_packages": 0,
        "voting_needed": defaultdict(int),
        "direct_merge": defaultdict(int),
        "package_details": {}
    }

    # Analyze each package
    for package_name, sources in package_groups.items():
        if len(sources) > 1:  # Packages with multiple sources
            results["multi_source_packages"] += 1
            package_result = {
                "source_count": len(sources),
                "voting_fields": [],
                "direct_merge_fields": [],
                "field_details": {}
            }

            # Check each entity field
            for field in entity_fields:
                # Collect non-empty values and their counts
                value_counts = defaultdict(int)
                total_sources_with_value = 0

                for source in sources:
                    value = source.get(field)
                    if value and str(value).strip():  # Non-empty values
                        value_str = str(value).strip()
                        value_counts[value_str] += 1
                        total_sources_with_value += 1

                # Store field details
                package_result["field_details"][field] = {
                    "values": dict(value_counts),
                    "total_sources": total_sources_with_value
                }

                # Determine if voting is needed
                if len(value_counts) > 1:
                    results["voting_needed"][field] += 1
                    package_result["voting_fields"].append(field)
                else:
                    results["direct_merge"][field] += 1
                    package_result["direct_merge_fields"].append(field)

            results["package_details"][package_name] = package_result

    return results


def print_results(results: Dict):
    TOTAL_PACKAGES = results["total_all_packages"]

    print(f"\nTotal number of packages: {results['total_packages']}")
    print(f"Number of multi-source packages: {results['multi_source_packages']}")

    print("\nEntity statistics that need voting:")
    for field, count in results["voting_needed"].items():
        percentage = (count / TOTAL_PACKAGES) * 100
        print(f"{field}: {count} packages need voting ({percentage:.2f}%)")

    print("\nEntity statistics that can be directly merged:")
    for field, count in results["direct_merge"].items():
        percentage = (count / TOTAL_PACKAGES) * 100
        print(f"{field}: {count} packages can be directly merged ({percentage:.2f}%)")

    print("\nPackage-level detailed analysis example (first 3 packages with conflicts):")
    count = 0
    for pkg, details in results["package_details"].items():
        if len(details["voting_fields"]) > 0:  # Only show packages with voting fields
            print(f"\nPackage name: {pkg}")
            print(f"Source count: {details['source_count']}")
            print("Fields that need voting:")
            for field in details["voting_fields"]:
                print(f"  {field}:")
                for value, freq in details["field_details"][field]["values"].items():
                    print(f"    - {value}: {freq} times")
            count += 1
            if count >= 3:
                break


def generate_latex_table(results: Dict):
    TOTAL_PACKAGES = results["total_all_packages"]

    # Generate LaTeX table
    latex_str = """
\\begin{table}[h]
\\caption{Entity Merging Statistics}
\\begin{tabular}{lccc}
\\hline
\\textbf{Entity Type} & \\textbf{Voting Needed} & \\textbf{Direct Merge} & \\textbf{Total} \\\\
\\hline
"""

    # Merge all fields
    all_fields = set(results["voting_needed"].keys()) | set(results["direct_merge"].keys())

    for field in sorted(all_fields):
        voting = results["voting_needed"].get(field, 0)
        direct = results["direct_merge"].get(field, 0)
        total = voting + direct
        voting_percent = (voting / TOTAL_PACKAGES) * 100
        direct_percent = (direct / TOTAL_PACKAGES) * 100

        latex_str += f"{field} & {voting} ({voting_percent:.2f}\\%) & {direct} ({direct_percent:.2f}\\%) & {total} \\\\\n"

    latex_str += """\\hline
\\end{tabular}
\\end{table}
"""
    print("\nLaTeX Table:")
    print(latex_str)


if __name__ == "__main__":
    file_path = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/Intelliradar_data.json"
    results = analyze_entities(file_path)
    print_results(results)
    generate_latex_table(results)  # Generate LaTeX table