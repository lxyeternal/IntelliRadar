# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : snk_osv_cmp.py
# @Project  : SCC_Intelligence
# Time      : 23/4/24 11:45 am
# Author    : honywen
# version   : python 3.8
# Description：
"""



import csv
import pandas as pd
from datetime import datetime


def read_ourdatabase():
    # 读取特定工作表
    pkg_manager = {"npm": [], "pypi": []}
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='all')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    for data in data_list:
        if data[1] == "npm":
            pkg_manager["npm"].append(data[0])
        else:
            pkg_manager["pypi"].append(data[0])
    return pkg_manager


def write_result_csv(data):
    with open("/Users/blue/Desktop/snyk_lookup.csv", "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(data)

def osv_database_check():
    pkg_manager = read_ourdatabase()
    with open("database/osv_database.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            print(row)
            pkgname = row[1].strip().lower()
            manager = row[0].strip().lower()
            if pkgname in pkg_manager[manager]:
                write_result_csv(row + ["TRUE"])
            else:
                write_result_csv(row + ["FALSE"])

def snyk_database_check():
    pkg_manager = read_ourdatabase()
    with open("database/snykdata_30.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            print(row)
            pkgname = row[1].strip().lower()
            manager = row[0].strip().lower()
            if manager == "pip":
                manager = "pypi"
            if pkgname in pkg_manager[manager]:
                write_result_csv(row + ["TRUE"])
            else:
                write_result_csv(row + ["FALSE"])

#  计算占比
def calculate_percentage(data):
    total_count = sum(count for _, count in data)
    # Calculating the percentage of each source's count in the total
    percentages = [(source, count / total_count * 100) for source, count in data]
    return percentages

def npm_source_sount():
    # 读取特定工作表
    npm_df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='npm')
    pypi_df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='pypi')
    # 将DataFrame转换为列表，每行一个列表
    all_source_pkgs = {}
    for df in [npm_df, pypi_df]:
        data_list = df.values.tolist()
        source_pkgs = {}
        for data in data_list:
            pkgname = data[0]
            source = data[6]
            if source not in source_pkgs:
                source_pkgs[source] = []
            if source not in all_source_pkgs:
                all_source_pkgs[source] = []
            source_pkgs[source].append(pkgname)
            all_source_pkgs[source].append(pkgname)
        # 创建一个字典来存储每个键的列表长度
        lengths = {key: len(value) for key, value in source_pkgs.items()}
        sorted_lengths = sorted(lengths.items(), key=lambda item: item[1], reverse=True)
        percentage_manager = calculate_percentage(sorted_lengths)
        print(sorted_lengths)
        print(percentage_manager)
    lengths = {key: len(value) for key, value in all_source_pkgs.items()}
    sorted_lengths = sorted(lengths.items(), key=lambda item: item[1], reverse=True)
    percentage_all = calculate_percentage(sorted_lengths)
    print(sorted_lengths)
    print(percentage_all)



def npm_date_gap():
    # 读取特定工作表
    with open('/Users/blue/Desktop/npm_data.csv', 'r') as f:
        reader = csv.reader(f)
        data_list = [row for row in reader]
    for data in data_list:
        pkgname = data[0]
        snyk_exist_flag = data[2]
        osv_exist_flag = data[3]
        release_date = data[4]
        our_discovery_date = data[5]
        source = data[6]
        snyk_discovery_date = data[7]
        osv_discovery_date = data[8]
        if snyk_exist_flag and our_discovery_date:
            snyk_discovery_date = datetime.strptime(snyk_discovery_date, '%d/%m/%y')
            our_discovery_date = datetime.strptime(our_discovery_date, '%d/%m/%y')
            date_gap = our_discovery_date - snyk_discovery_date
            print(pkgname, date_gap.days)
        # if "T" in release_date:
        #     release_date = release_date.split("T")[0]  # 移除时间部分
        #     # 将日期从 "年-月-日" 转换为 "日/月/年" 的两位年份
        #     formatted_release_date = datetime.strptime(release_date, '%Y-%m-%d').strftime('%d/%m/%y')
        #     data[4] = formatted_release_date
        # if "T" in our_discovery_date:
        #     our_discovery_date = our_discovery_date.split("T")[0]  # 移除时间部分
        #     # 将日期从 "年-月-日" 转换为 "日/月/年" 的两位年份
        #     formatted_discovery_date = datetime.strptime(our_discovery_date, '%Y-%m-%d').strftime('%d/%m/%y')
        #     data[5] = formatted_discovery_date
    # with open("/Users/blue/Desktop/new_pypi_data.csv", "w") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(data_list)



import os
import csv
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

def snyk_date_info(driver, pageurl, pkgname):
    driver.get(pageurl)
    driver.implicitly_wait(10)
    if "No results found" in driver.page_source:
        return "None"
    vulns_table = driver.find_element(By.CLASS_NAME, "vulns-table")
    table_tbody = vulns_table.find_element(By.CLASS_NAME, "vue--table__tbody")
    vue_table_row = table_tbody.find_elements(By.TAG_NAME, "tr")[:1]
    malpkg_info = {}
    for row_index, row in enumerate(vue_table_row):
        row_tds = row.find_elements(By.TAG_NAME, "td")
        formatted_date = ""
        for td_index, td in enumerate(row_tds):
            if td_index == 0:
                td_type = td.text.split("\n")[1].strip()
                td_href = td.find_element(By.TAG_NAME, "a").get_attribute('href').strip()
                if td_type != 'Malicious Package':
                    continue
            if td_index == 1:
                pkgname = td.text.split(" ")[0].strip()
                pkgversion = td.text.replace(pkgname, "").strip()
            if td_index == 3:
                timedata = td.text.strip()
                date_obj = datetime.strptime(timedata, "%d %b %Y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
        malpkg_info[pkgname] = formatted_date
    if malpkg_info:
        try:
            formatted_date = malpkg_info[pkgname]
        except:
            formatted_date = "None"
        return formatted_date
    else:
        return "None"


def write_snyk_time_(pkgname, date):
    with open("/Users/blue/Desktop/our_snyk_time.csv", "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([pkgname, date])


def github_snyk_time():
    service = Service(executable_path="/Users/blue/Documents/GitHub/SCC_Intelligence/utils/chromedriver/macarm/chromedriver")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    with open("/Users/blue/Desktop/test.csv", "r") as csvfile:
        csv_reader = csv.reader(csvfile)
        for index, row in enumerate(csv_reader):
            pkgname = row[0].strip()
            try:
                published_date = snyk_date_info(driver, "https://security.snyk.io/vuln/pip?search=" + pkgname, pkgname)
                write_snyk_time_(pkgname, published_date)
            except:
                write_snyk_time_(pkgname, "None")


def big_query_pypi():
    # 读取特定工作表
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='pypi')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    content = ""
    for data in data_list:
        day_gap = data[10]
        try:
            if int(day_gap) == 11:
                content += "file.project = " + "\"" + data[0] + "\"" + " OR "
        except:
            pass
    print(content)



def manager_count():
    # 读取特定工作表
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='pkg_source')
    # 将DataFrame转换为列表，每行一个列表
    pypi_count = {}
    npm_count = {}
    data_list = df.values.tolist()
    for data in data_list:
        manager = data[1]
        source = data[6]
        if manager == "pypi":
            if source not in pypi_count:
                pypi_count[source] = 1
            else:
                pypi_count[source] += 1
        else:
            if source not in npm_count:
                npm_count[source] = 1
            else:
                npm_count[source] += 1
    pypi_count["phylum"] = 3609
    npm_count["github"] = 7513
    sorted_pypi_count = {key: value for key, value in sorted(pypi_count.items(), key=lambda item: item[1], reverse=True)}
    sorted_npm_count = {key: value for key, value in sorted(npm_count.items(), key=lambda item: item[1], reverse=True)}

    pypi_count_total = sum(sorted_pypi_count.values())
    # 计算每个键的值占总和的比例，并打印结果
    pypi_count_ratios = {key: value / pypi_count_total for key, value in sorted_pypi_count.items()}

    npm_count_total = sum(sorted_npm_count.values())
    # 计算每个键的值占总和的比例，并打印结果
    npm_count_ratios = {key: value / npm_count_total for key, value in sorted_npm_count.items()}

    print(sorted_pypi_count)
    print(pypi_count_ratios)
    print(sorted_npm_count)
    print(npm_count_ratios)