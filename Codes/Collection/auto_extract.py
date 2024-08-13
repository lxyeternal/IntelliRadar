# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : test.py
# @Project  : PMonitor
# Time      : 18/1/24 10:42 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from Configs.config import HEADER
from readability import Document
from urllib.parse import urlparse
from selenium.webdriver.chrome.service import Service


class AutoExtract:
    def __init__(self):
        self.chromedriver = '../../utils/chromedriver/macarm/chromedriver'
        self.service = Service(executable_path=self.chromedriver)
        self.options = webdriver.ChromeOptions()


    def parsetable(self, table_element):
        # 提取表头
        table_content = ""
        header_row = table_element.find('tr')
        headers = [th.text.strip() for th in header_row.find_all('th')]
        table_content = table_content + '\n' + ' '.join(headers)
        # 提取表格的每一行
        for tr in table_element.find_all('tr')[1:]:  # 跳过表头行
            row = [td.text.strip() for td in tr.find_all('td')]
            table_content = table_content + '\n' + '  '.join(row)
        return table_content


    def parsecodes(self, page_element):
        codes = ""
        for code in page_element.find_all('code'):
            codes = codes + '\n' + code.text.strip()
        return codes


#  suit for medium,
    def extract_body(self, doc):
        page_content = ""
        if doc.summary().startswith("<html>"):
            soup = BeautifulSoup(doc.summary(), "html.parser")
            for tag in soup.find_all(recursive=True):  # True 使得 find_all 返回所有标签
                if tag.name == "table":
                    table_content = self.parsetable(tag)
                    page_content = page_content + '\n' + table_content
                else:
                    page_content = page_content + '\n' + tag.text.strip()
        else:
            page_content = doc.summary()
        return page_content

    def phylumblog(self, pagelink):
        page_content = ""
        response = requests.get(pagelink, headers=HEADER)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            post_title = soup.find(class_='post-title').text
            gh_content = soup.find(class_='gh-content')
            for element in gh_content.find_all(True, recursive=False):  # 遍历所有元素，不包括子元素
                if element.name in ['p', 'h1', 'h2', 'h3', 'code', 'table']:
                    if element.name == 'table':
                        table_content = self.parsetable(element)
                        page_content = page_content + '\n' + table_content
                    else:
                        page_content = page_content + '\n' + element.text.strip()
                else:
                    # 对其他标签直接提取文本
                    text = element.get_text().strip()
                    page_content = page_content + '\n' + text
        return page_content


    def requests_request(self, pagelink):
        response = requests.get(pagelink, headers=HEADER)
        doc = Document(response.content)
        return doc


    def selenium_request(self, pagelink):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.get(pagelink)
        driver.implicitly_wait(10)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        html = driver.page_source
        doc = Document(html)
        driver.close()
        return doc


    def auto_select(self, pagelink):
        parsed_url = urlparse(pagelink)
        url_domain = parsed_url.netloc
        if url_domain == "blog.phylum.io":
            page_content = self.phylumblog(pagelink)
        elif url_domain == "medium.com":
            # doc = self.requests_request(pagelink)
            doc = self.selenium_request(pagelink)
            page_content = self.extract_body(doc)
        elif url_domain == "www.bleepingcomputer.com":
            doc = self.selenium_request(pagelink)
            page_content = self.extract_body(doc)
        else:
            pass
        print(page_content)


if __name__ == '__main__':
    auto = AutoExtract()
    # auto.auto_select("https://www.bleepingcomputer.com/news/security/10-malicious-pypi-packages-found-stealing-developers-credentials/#google_vignette")
    # auto.auto_select("https://blog.phylum.io/large-typosquat-campaign-targeting-react-and-angular/")
    # auto.auto_select("https://medium.com/checkmarx-security/the-skeleton-squad-tracing-the-origins-and-scope-of-5000-malicious-packages-on-pypi-7516c16e4da9")
    auto.auto_select("https://medium.com/checkmarx-security/pypi-on-hold-suspends-new-users-and-projects-creations-due-to-a-high-volume-of-malicious-activity-7ff09cd25f3e")