# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : time_mapping.py
# @Project  : SCC_Intelligence
# Time      : 10/4/24 10:42 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


import csv
import json
import pandas as pd


def read_raw_txt():
    webpage_dict = {}
    raw_data = []
    with open("pagelinks/raw_webpage.txt", "r") as csvfile:
        content_lines = csvfile.readlines()
        for row in content_lines:
            row_split = row.strip().split("\t")
            raw_data.append(row_split)
            source = row_split[0]
            page_url = row_split[1]
            if source in webpage_dict:
                webpage_dict[source].append(page_url)
            else:
                webpage_dict[source] = [page_url]
    return webpage_dict, raw_data

def read_time_txt():
    time_dict = {}
    time_data = []
    with open("pagelinks/old_time_webpage.txt", "r") as csvfile:
        content_lines = csvfile.readlines()
        for row in content_lines:
            row_split = row.strip().split("\t")
            time_data.append(row_split)
            source = row_split[1]
            page_url = row_split[3]
            if source in time_dict:
                time_dict[source].append(page_url)
            else:
                time_dict[source] = [page_url]
    return time_dict, time_data

def consistency_check():
    webpage_dict = read_raw_txt()
    time_dict = read_time_txt()
    for source in webpage_dict:
        if source in time_dict:
            if len(webpage_dict[source]) != len(time_dict[source]):
                print("Inconsistent data for source: ", source)
            else:
                print("Consistent data for source: ", source)
        else:
            print("No time data for source: ", source)


def consistency_txt():
    webpage_dict, raw_data = read_raw_txt()
    time_dict, time_data = read_time_txt()
    with open("pagelinks/consistency.txt", "w") as txtfile:
        for raw_source in raw_data:
            flag = 0
            source = raw_source[0].strip()
            page_url = raw_source[1].strip()
            for time_source in time_data:
                first = time_source[0].strip()
                second = time_source[1].strip()
                timedata = time_source[2].strip()
                time_page_url = time_source[3].strip()
                if source == second:
                    if page_url == time_page_url:
                        flag = 1
                        break
            if flag == 1:
                txtfile.write(first + "\t" + source + "\t" + timedata + "\t" + time_page_url + "\t")
                txtfile.write("\n")
            else:
                txtfile.write(first + "\t" + source + "\t" + "None" + "\t" + page_url + "\t")
                txtfile.write("\n")

import os
import csv
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

def snyk_date_info(driver, pageurl):
    driver.get(pageurl)
    driver.implicitly_wait(10)
    vulns_table = driver.find_element(By.CLASS_NAME, "vulns-table")
    table_tbody = vulns_table.find_element(By.CLASS_NAME, "vue--table__tbody")
    vue_table_row = table_tbody.find_elements(By.TAG_NAME, "tr")[:1]
    for row_index, row in enumerate(vue_table_row):
        row_tds = row.find_elements(By.TAG_NAME, "td")
        formatted_date = ""
        flag = "0"
        for td_index, td in enumerate(row_tds):
            if td_index == 0:
                td_type = td.text.split("\n")[1].strip()
                td_href = td.find_element(By.TAG_NAME, "a").get_attribute('href').strip()
                if td_type == 'Malicious Package':
                    flag = "1"
            if td_index == 1:
                pkgname = td.text.split(" ")[0].strip()
                pkgversion = td.text.replace(pkgname, "").strip()
            if td_index == 3:
                timedata = td.text.strip()
                date_obj = datetime.strptime(timedata, "%d %b %Y")
                # 将日期对象格式化为所需的字符串格式
                formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date


def write_snyk_time_(pkgname, exist_flag, date):
    with open("/Users/blue/Desktop/our_snyk_time.csv", "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([pkgname, exist_flag, date])

def github_snyk_time():
    service = Service(executable_path="/Users/blue/Documents/GitHub/SCC_Intelligence/utils/chromedriver/macarm/chromedriver")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    with open("/Users/blue/Desktop/snyk_lookup.csv", "r") as csvfile:
        csv_reader = csv.reader(csvfile)
        for index, row in enumerate(csv_reader):
            pkgname = row[0].strip()
            exist_flag = row[1].strip()
            if exist_flag == "TRUE":
                try:
                    published_date = snyk_date_info(driver, "https://security.snyk.io/vuln?search=" + pkgname)
                    print(pkgname, exist_flag, published_date)
                    write_snyk_time(pkgname, exist_flag, published_date)
                except:
                    print("Error: ", pkgname)
                    write_snyk_time(pkgname, exist_flag, "")
            else:
                write_snyk_time(pkgname, exist_flag, "")


def write_snyk_time(data):
    with open("/Users/blue/Desktop/newtest.csv", "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(data)


def check_snyk_time():
    service = Service(executable_path="/Users/blue/Documents/GitHub/SCC_Intelligence/utils/chromedriver/macarm/chromedriver")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    with open("/Users/blue/Desktop/new_phylum_pkgs.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            pkgname = row[0].strip()
            exist_flag = row[-3].strip()
            if exist_flag == "TRUE":
                try:
                    published_date = snyk_date_info(driver, "https://security.snyk.io/vuln?search=" + pkgname)
                    print(pkgname, exist_flag, published_date)
                    write_snyk_time(row + [published_date])
                except:
                    print("Error: ", pkgname)
                    write_snyk_time(row + ["None"])
            else:
                write_snyk_time(row + ["None"])


def our_file_package_time():
    old_time_dict = {}
    with open("pagelinks/old_time_webpage.txt", "r") as csvfile:
        content_lines = csvfile.readlines()
        for index, row in enumerate(content_lines):
            row_split = row.strip().split("\t")
            source = row_split[1].lower()
            timedata = row_split[2]
            if source in old_time_dict:
                old_time_dict[source].append((len(old_time_dict[source]) + 1, timedata))
            else:
                old_time_dict[source] = [(1, timedata)]
    with open("/Users/blue/Desktop/MalData.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_source = row[-1].strip().lower()
            row_filename = row[-2].strip()
            flag = 0
            if row_source in ["socket", "sonatype", "github", "qianxin", "datadog", "medium", "ifrog", "medium_recommand", "snyk", "checkmarx"]:
                row_filename = row_filename.split("/")[-1].replace("_.json", "").replace("_gpt4.json", "").replace(".json", "").replace(row_source+'_', "").replace("checkmarx_", "").strip()
                if row_source in old_time_dict:
                    for item in old_time_dict[row_source]:
                        if str(item[0]) == row_filename:
                            flag = 1
                            write_snyk_time(row + [item[1]])
                            print(row_source, row_filename, item[1])
                            break
                if flag == 0:
                    write_snyk_time(row + ["None"])
                    print(row_source, row_filename, "None")
            else:
                write_snyk_time(row + ["None"])
                print(row_source, row_filename, "None")



def new_our_file_package_time():
    old_time_dict = {}
    with open("pagelinks/new_time_webpage.txt", "r") as csvfile:
        content_lines = csvfile.readlines()
        for index, row in enumerate(content_lines):
            row_split = row.strip().split("\t")
            timestamp = row_split[0]
            source = row_split[1].lower()
            timedata = row_split[2]
            if source in old_time_dict:
                old_time_dict[source].append((timestamp, timedata))
            else:
                old_time_dict[source] = [(timestamp, timedata)]
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/Analysis/MalData.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            if index < 7674:
                continue
            row_source = row[-1].strip().lower()
            row_filename = row[-2].strip()
            flag = 0
            row_filename = row_filename.split("/")[-1].replace("_gpt4.json", "").replace(".json", "").strip()
            print(row_filename)
            if row_source in old_time_dict:
                for item in old_time_dict[row_source]:
                    if item[0] == row_filename:
                        flag = 1
                        write_snyk_time(row + [item[1]])
                        break
            if flag == 0:
                write_snyk_time(row + ["None"])
        # else:
        #     write_snyk_time(row)
        #     print(row_source, row_filename, "None")


def get_github_release_date():
    pkg_release_date = {}
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/analysis_data/registry_npmjs.json", "r") as f:
        data = json.load(f)
        for index, item in enumerate(data):
            pkgname = item.get("任务源网址", "").split("/")[-1].strip()
            metainfo = item.get("字段3", {})
            try:
                metainfo = json.loads(metainfo)
                if metainfo:
                    time_list = list()
                    release_date = metainfo.get("time", {})
                    if release_date:
                        create_time = release_date.get("created", "")
                    # for key in release_date:
                    #     if key == "unpublished":
                    #         continue
                    #     time_list.append(release_date[key].strip())
                    # time_list.sort()
                        pkg_release_date[pkgname] = create_time
                else:
                    pkg_release_date[pkgname] = "None"
            except:
                pass
    print(pkg_release_date)
    with open("/Users/blue/Desktop/github_maldata.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[2].strip()
            if row_filename in pkg_release_date:
                release_date = pkg_release_date[row_filename]
                write_snyk_time(row + [release_date])
            else:
                write_snyk_time(row + ["None"])


def parse_bq_date():
    bq_date = {}
    new_bq_date = {}
    with open("/Users/blue/Downloads/bq-results-phylum.json", "r") as f:
        f_lines = f.readlines()
        for f_line in f_lines:
            data = json.loads(f_line)
            pkgname = data.get("name", "").strip()
            version = data.get("version", "").strip()
            upload_time = data.get("upload_time", "").strip().split(" ")[0]
            if pkgname in bq_date:
                bq_date[pkgname].append(upload_time)
            else:
                bq_date[pkgname] = [upload_time]
    for key in bq_date:
        new_bq_date[key] = sorted(list(set(bq_date[key])))[0]
    with open("/Users/blue/Desktop/new_phylum_pkgs.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            if row_filename in new_bq_date:
                upload_time = new_bq_date[row_filename]
                write_snyk_time(row + [upload_time])
            else:
                write_snyk_time(row + ["None"])


def write_csv(csv_file, data):
    with open(csv_file, "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(data)

def github_snyk_osv_time():
    osv_pkg_date = {}
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/SnykCheck/database/osv_database.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            pkgmanager = row[0].strip()
            pkgname = row[1].strip()
            date = row[2].strip()
            if pkgmanager == "npm":
                osv_pkg_date[pkgname] = date

    with open("/Users/blue/Desktop/github_snyk_time.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            if row_filename in osv_pkg_date:
                osv_upload_time = osv_pkg_date[row_filename]
                write_csv("/Users/blue/Desktop/github_snyk_osv_time.csv", row + [osv_upload_time])
            else:
                write_csv("/Users/blue/Desktop/github_snyk_osv_time.csv", row + ["None"])



def our_osv_check():
    osv_pkg_date = {}
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/SnykCheck/database/osv_database.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            pkgmanager = row[0].strip()
            pkgname = row[1].strip()
            date = row[2].strip()
            osv_pkg_date[pkgname] = date
    with open("/Users/blue/Desktop/new_phylum_pkgs.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip().lower()
            if row_filename in osv_pkg_date:
                osv_upload_time = osv_pkg_date[row_filename]
                write_csv("/Users/blue/Desktop/our_osv_time.csv", row + ["True", osv_upload_time])
            else:
                write_csv("/Users/blue/Desktop/our_osv_time.csv", row + ["False", "None"])


from typing import Dict, List, Tuple, Optional


def find_earliest_str(data: Dict[str, List[Tuple[str, Optional[str]]]]) -> Dict[str, Tuple[str, Optional[str]]]:
    result = {}
    for key, values in data.items():
        valid_entries = sorted((entry for entry in values if entry[1] is not None), key=lambda x: x[1])
        if valid_entries:
            result[key] = valid_entries[0]
        else:
            result[key] = values[0]
    return result


def our_newsdate():
    maldata_time = {}
    with open("/Users/blue/Desktop/MalData_newtime.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            date_time = row[-1].strip().split("T")[0]
            if "-" in date_time:
                pass
            elif date_time == "None":
                pass
            else:
                date_time = datetime.strptime(date_time, "%d/%m/%y").strftime("%Y-%m-%d")
            data_source = row[-2].strip()
            if row_filename in maldata_time:
                maldata_time[row_filename].append((data_source, date_time))
            else:
                maldata_time[row_filename] = [(data_source, date_time)]
    maldata_time = find_earliest_str(maldata_time)
    with open("/Users/blue/Desktop/our_snyk_osv_time.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            if row_filename in maldata_time:
                write_csv("/Users/blue/Desktop/newnewnewnew.csv", row + [maldata_time[row_filename][0], maldata_time[row_filename][1]])
            else:
                write_csv("/Users/blue/Desktop/newnewnewnew.csv", row + ["None", "None"])

def our_release_pypi_date():
    maldata_release = {}
    with open("/Users/blue/Desktop/test.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            date_time = row[-1].strip()
            maldata_release[row_filename] = date_time
    with open("/Users/blue/Desktop/our_snyk_osv_time_news.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            if row_filename in maldata_release:
                write_csv("/Users/blue/Desktop/newnewnewnew.csv", row + [maldata_release[row_filename]])
            else:
                write_csv("/Users/blue/Desktop/newnewnewnew.csv", row + ["None"])


def our_release_npm_date():
    pkg_release_date = {}
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/analysis_data/registry_npmjs.json", "r") as f:
        data = json.load(f)
        for index, item in enumerate(data):
            pkgname = item.get("任务源网址", "").split("/")[-1].strip()
            metainfo = item.get("字段3", {})
            try:
                metainfo = json.loads(metainfo)
                if metainfo:
                    release_date = metainfo.get("time", {})
                    if release_date:
                        create_time = release_date.get("created", "").split("T")[0]
                        pkg_release_date[pkgname] = create_time
                else:
                    pkg_release_date[pkgname] = "None"
            except:
                pass
    with open("/Users/blue/Desktop/our_snyk_osv_time_news_release.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            release_time = row[-1].strip()
            if release_time == "None":
                if row_filename in pkg_release_date:
                    release_date = pkg_release_date[row_filename]
                    row[-1] = release_date
                    write_csv("/Users/blue/Desktop/newnewnewnew.csv", row)
                else:
                    write_csv("/Users/blue/Desktop/newnewnewnew.csv", row)
            else:
                write_csv("/Users/blue/Desktop/newnewnewnew.csv", row)

def add_manager_pypi_our():
    bq_date = []
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/analysis_data/bq-results-pypi.json", "r") as f:
        f_lines = f.readlines()
        for f_line in f_lines:
            data = json.loads(f_line)
            pkgname = data.get("name", "").strip()
            bq_date.append(pkgname)
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/Analysis/our_snyk_osv_release_news_source_snyk_osv.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            if row_filename in bq_date:
                write_csv("/Users/blue/Desktop/newnewnewnewnew.csv", row + ["pypi"])
            else:
                write_csv("/Users/blue/Desktop/newnewnewnewnew.csv", row + ["None"])


def add_manager_npm_our():
    pkg_release_date = []
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/analysis_data/registry_npmjs.json", "r") as f:
        data = json.load(f)
        for index, item in enumerate(data):
            pkgname = item.get("任务源网址", "").split("/")[-1].strip()
            metainfo = item.get("字段3", {})
            pkg_release_date.append(pkgname)
    with open("/Users/blue/Desktop/newnewnewnewnew.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            row_manager = row[-1].strip()
            if row_manager == "None":
                if row_filename in pkg_release_date:
                    row[-1] = "npm"
                    write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", row)
                else:
                    write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", row)
            else:
                write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", row)

def calaulate_daygap():
    with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/Analysis/our_snyk_osv_release_news_source_snyk_osv.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for index, row in enumerate(csvreader):
            row_filename = row[0].strip()
            row_release = row[4].strip()
            row_news = row[5].strip()
            row_snyk = row[7].strip()
            row_osv = row[8].strip()
            print(row_filename, row_release, row_news, row_snyk, row_osv)



def raw_data_manager():
    # 读取特定工作表
    pkg_manager = {}
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='pypi')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    for data in data_list:
        pkgname = data[0].strip()
        manager = data[1].strip()
        pkg_manager[pkgname] = manager
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='all_raw_data')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    for data in data_list:
        pkgname = data[0]
        if pkgname in pkg_manager:
            write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", data + [pkg_manager[pkgname]])
        else:
            write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", data + ["None"])



def check_manager():
    # 读取特定工作表
    pkg_manager = {}
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='all')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    for data in data_list:
        pkgname = str(data[0]).lower()
        manager = data[1]
        pkg_manager[pkgname] = manager
    df = pd.read_excel('/Users/blue/Desktop/npm_pypi_compare.xlsx', sheet_name='all_raw_data')
    # 将DataFrame转换为列表，每行一个列表
    data_list = df.values.tolist()
    for data in data_list:
        pkgname = str(data[0]).lower()
        if pkgname in pkg_manager:
            write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", data + [pkg_manager[pkgname]])
        else:
            write_csv("/Users/blue/Desktop/newnewnewnewnew123.csv", data + ["None"])




# our_osv_check()
check_manager()