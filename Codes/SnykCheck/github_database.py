# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : github_database.py
# @Project  : SCC_Intelligence
# Time      : 6/4/24 8:37 pm
# Author    : default
# version   : python 3.8
# Description：
"""

import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GithubDatabase:
    def __init__(self):
        self.github = "https://github.com/advisories?page={}&query=type%3Amalware+ecosystem%3Anpm"
        self.chromedriver = '../../utils/chromedriver/macarm/chromedriver'
        self.github_sourcelink = "github_sourcelink.txt"
        self.github_database_csv = "github_database.csv"
        self.collected_links = []
        self.webpage_links = []
        self.collected_manager_links = []
        self.service = Service(executable_path=self.chromedriver)
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=self.service, options=self.options)


    def load_webpage_links(self):
        with open("/codes/Collection/pagelinks/webpage.txt", "r", encoding="utf-8") as file:
            for line in file:
                source, link = line.strip().split('\t')
                if source == "github":
                    self.webpage_links.append(link)

    def write_data_csv(self, data):
        with open(self.github_database_csv, "a", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(data)

    def write_link_file(self, manager, data):
        with open(self.github_sourcelink, "a", encoding="utf-8") as file:
            file.write(manager + '\t' + data + "\n")

    def load_processed_files(self):
        with open(self.github_sourcelink, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    manager, data = line.split('\t')
                    self.collected_links.append(data)
                    self.collected_manager_links.append((manager, data))

    def github_blog_link(self):
        for page_index in range(1, 401):
            page_url = self.github.format(page_index)
            self.driver.get(page_url)
            time.sleep(5)
            self.driver.implicitly_wait(10)
            navigation_container = self.driver.find_element(By.CLASS_NAME, "js-active-navigation-container")
            navigation_items = navigation_container.find_elements(By.CLASS_NAME, "js-navigation-item")
            for navigation_item in navigation_items:
                href_value = navigation_item.find_element(By.TAG_NAME, "a").get_attribute("href")
                if href_value in self.collected_links:
                    continue
                self.write_link_file("npm", href_value)

    def github_content(self):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        for manager_name, page_url in self.collected_manager_links:
            if page_url in self.webpage_links:
                continue
            driver.get(page_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            article_main = driver.find_element(By.TAG_NAME, "main")
            Subhead_description = article_main.find_element(By.CLASS_NAME, "Subhead-description")
            v_align_middle = Subhead_description.find_element(By.CLASS_NAME, "v-align-middle").text.strip()
            datatime = Subhead_description.find_element(By.TAG_NAME, "relative-time").get_attribute("datetime").strip()
            table_content = article_main.find_element(By.CSS_SELECTOR, ".gutter-lg.gutter-condensed.clearfix")
            name_manager = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-12.col-md-6.pr-md-2")
            package_name = name_manager.find_element(By.CSS_SELECTOR, ".f4.color-fg-default.text-bold").text.strip()
            manager_name = name_manager.find_element(By.CSS_SELECTOR, ".color-fg-muted.f4.d-inline-flex").text
            manager_name = manager_name.replace("(", "").replace(")", "").strip()
            version_div = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-6.col-md-3.py-2.py-md-0.pr-2")
            version = version_div.find_element(By.CSS_SELECTOR, ".f4.color-fg-default").text.strip()
            description_div = table_content.find_element(By.CSS_SELECTOR, ".Box-body.px-5.pb-5")
            description = description_div.text.strip()
            right_table = article_main.find_element(By.CSS_SELECTOR, ".col-12.col-md-3.float-left.pt-3.pt-md-0")
            weakness = right_table.find_element(By.CSS_SELECTOR,".discussion-sidebar-item.js-repository-advisory-details").text.replace("Weaknesses", "").strip()
            print(v_align_middle, datatime, package_name, manager_name, version, weakness)
            self.write_data_csv([v_align_middle, datatime, package_name, manager_name, version, description, weakness])
        driver.quit()


if __name__ == '__main__':
    github = GithubDatabase()
    # github.github_blog_link()
    github.load_webpage_links()
    github.load_processed_files()
    github.github_content()