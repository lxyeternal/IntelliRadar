# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : compare_snyk.py
# @Project  : SCC_Intelligence
# Time      : 6/4/24 5:24 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""

import csv

def read_csv(file):
    csv_data = []
    with open(file, "r", encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            csv_data.append(row)
    return csv_data


def extract_packages():
    csv_data = read_csv("MalData.csv")
    packages = set()
    for row in csv_data:
        packages.add(row[0].strip())
    query = ""
    for package in packages:
        if package != "":
            query = "name = " + "\"" + package + "\"" + " or " + query
    print(query)
    return query


def compare_lists(list1, list2):
    common_elements = set(list1).intersection(set(list2))
    common_elements_count = len(common_elements)
    unique_to_list1_count = len(set(list1) - set(list2))
    unique_to_list2_count = len(set(list2) - set(list1))
    print(common_elements_count, unique_to_list1_count, unique_to_list2_count)
    return common_elements_count, unique_to_list1_count, unique_to_list2_count

def compare_snyk():
    snyk_csv = read_csv("database/snykdata_30.csv")
    snyk_packages = set()
    for row in snyk_csv:
        snyk_packages.add(row[1].strip())

    sccint_csv = read_csv("MalData.csv")
    sccint_packages = set()
    for row in sccint_csv:
        sccint_packages.add(row[0].strip())

    compare_lists(sccint_packages, snyk_packages)

    # github_csv = read_csv("../Analysis/github_maldata.csv")
    # github_packages = set()
    # for row in github_csv:
    #     sccint_packages.add(row[2].strip())
    # Find the intersection between the two sets
    common_packages = sccint_packages.intersection(snyk_packages)
    # Calculate the number of common packages and their proportion in sccint
    common_count = len(common_packages)
    sccint_proportion = common_count / len(sccint_packages) if sccint_packages else 0
    # Calculate the proportion in snyk
    snyk_proportion = common_count / len(snyk_packages) if snyk_packages else 0

    return {
        "common_count": common_count,
        "sccint_proportion": sccint_proportion,
        "snyk_proportion": snyk_proportion,
        "sccint_total": len(sccint_packages),
        "snyk_total": len(snyk_packages)
    }


collected_packages = extract_packages()
# Usage example
result = compare_snyk()
print(f"Common Packages Count: {result['common_count']}")
print(f"Proportion in SCCINT: {result['sccint_proportion'] * 100:.2f}%")
print(f"Proportion in SNYK: {result['snyk_proportion'] * 100:.2f}%")
print(f"Total in SCCINT: {result['sccint_total']}")
print(f"Total in SNYK: {result['snyk_total']}")

