# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : snykdata.py
# @Project  : SCC_Intelligence
# Time      : 6/4/24 10:39 am
# version   : python 3.8
# Description：
"""


import os
import csv
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


class SnykData:
    def __init__(self):
        self.record_file = "database/snykdata_30.csv"
        self.chromedriver = "../../utils/chromedriver/macarm/chromedriver"
        self.snyk_baseurl = "https://security.snyk.io/"
        self.synk_vulurl = "https://security.snyk.io/vuln/"
        service = Service(executable_path=self.chromedriver)
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)


    def write_data_csv(self, data):
        with open(self.record_file, "a") as f:
            writer = csv.writer(f)
            writer.writerow(data)

    def parse_snyk_database(self, manager, page_index):
        print(os.path.join(self.synk_vulurl, manager, page_index))
        self.driver.get(os.path.join(self.synk_vulurl, manager, page_index))
        self.driver.implicitly_wait(10)
        vulns_table = self.driver.find_element(By.CLASS_NAME, "vulns-table")
        table_tbody = vulns_table.find_element(By.CLASS_NAME, "vue--table__tbody")
        vue_table_row = table_tbody.find_elements(By.TAG_NAME, "tr")
        for row_index, row in enumerate(vue_table_row):
            row_tds = row.find_elements(By.TAG_NAME, "td")
            pkgname = ""
            pkgversion = ""
            td_href = ""
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
                    formatted_date = date_obj.strftime("%Y-%m-%d")
            if flag == "1":
                print(manager, pkgname, pkgversion, formatted_date, td_href)
                self.write_data_csv([manager, pkgname, pkgversion, formatted_date, td_href])


    def data_collect(self):
        for page_index in range(1, 31):
            self.parse_snyk_database("pip", str(page_index))


if __name__ == '__main__':
    snykdata = SnykData()
    snykdata.data_collect()