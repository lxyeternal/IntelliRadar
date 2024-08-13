# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : phylum_blog.py
# @Project  : PMonitor
# Time      : 17/1/24 10:53 am
# Author    : honywen
# version   : python 3.8
# Description：
"""


import requests
from bs4 import BeautifulSoup


def parsetable(table_element):
    # 提取表头
    header_row = table_element.find('tr')
    headers = [th.text.strip() for th in header_row.find_all('th')]
    print('  '.join(headers))

    # 提取表格的每一行
    for tr in table_element.find_all('tr')[1:]:  # 跳过表头行
        row = [td.text.strip() for td in tr.find_all('td')]
        print('  '.join(row))


def PhylumBlog():
    blogurl = "https://blog.phylum.io/large-typosquat-campaign-targeting-react-and-angular/"
    response = requests.get(blogurl)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        post_title = soup.find(class_='post-title').text
        gh_content = soup.find(class_='gh-content')
        for element in gh_content.find_all(True, recursive=False):  # 遍历所有元素，不包括子元素
            if element.name in ['p', 'h1', 'h2', 'h3', 'code', 'table']:
                if element.name == 'table':
                    parsetable(element)
                else:
                    print(element.text)
            else:
                # 对其他标签直接提取文本
                text = element.get_text()
                print(text)


PhylumBlog()
