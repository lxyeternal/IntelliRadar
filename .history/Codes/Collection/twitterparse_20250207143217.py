# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : sonatype.py
# @Project  : PMonitor
# Time      : 16/1/24 4:02 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""
import time

from selenium import webdriver
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


# 寻找标题
def is_header_class(tag):
    """
    检查元素的class属性是否包含'header'或类似的字样。
    :param tag: BeautifulSoup标签
    :return: 如果包含，则为True
    """
    if 'class' in tag.attrs:
        class_names = [cls.lower() for cls in tag.get('class', [])]
        return any('header' in cls for cls in class_names)
    return False

# 寻找正文

def has_long_text_siblings(tag, window=3, min_length=10):
    """
    检查标签及其指定窗口内的兄弟元素是否包含长文本。
    :param tag: BeautifulSoup标签
    :param window: 考虑的兄弟元素数量（前后）
    :param min_length: 认为文本“长”的最小长度
    :return: 如果标签及其周围兄弟元素包含长文本，则为True
    """
    if not tag or tag.name != 'p' or len(tag.get_text(strip=True).split()) < min_length:
        return False
    # 检查前面的兄弟元素
    prev_siblings = tag.find_all_previous("p", limit=window)
    if not any(len(sibling.get_text(strip=True).split()) > min_length for sibling in prev_siblings):
        return False
    # 检查后面的兄弟元素
    next_siblings = tag.find_all_next("p", limit=window)
    if not any(len(sibling.get_text(strip=True).split()) > min_length for sibling in next_siblings):
        return False
    return True

def extract_header_context(url):
    chromedriver = '../../utils/chromedriver/macarm/chromedriver'
    service = Service(executable_path=chromedriver)
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--enable-javascript")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    driver = webdriver.Chrome(service=service, options=options)
    # 导航到网站
    driver.get(url)
    # 等待页面加载（可选：使用显式/隐式等待）
    time.sleep(10)
    driver.implicitly_wait(10)
    # 获取网页源代码
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    # 寻找标题并去重
    titles = set()  # 使用集合来自动去重
    # 检查标准标题标签
    for header_tag in ['h1', 'h2', 'h3']:
        for header in soup.find_all(header_tag):
            title_text = header.get_text().strip()
            titles.add(title_text)  # 集合自动处理重复项

    # 检查类名包含'header'的元素
    for tag in soup.find_all(is_header_class):
        title_text = tag.get_text().strip()
        titles.add(title_text)

    filtered_titles = {title for title in titles if 4 <= len(title.split()) <= 50}
    filtered_titles = sorted(filtered_titles, key=lambda title: len(title.split()), reverse=True)[:3]

    # 寻找正文区域
    content = []
    for paragraph in soup.find_all('p'):
        if has_long_text_siblings(paragraph):
            parent = paragraph.find_parent()  # 找到包含正文的根节点
            if parent and parent not in content:
                content.append(parent)  # 避免重复添加相同的根节点
    print(content)
    return(filtered_titles, content)


def extract_content(element, content_list):
    if element.name in ['p', 'h2', 'h3']:
        content_list.append(element.text)
    elif element.name in ['ul', 'ol']:
        for li in element.find_all('li', recursive=False):
            extract_content(li, content_list)
    elif element.name == 'li':
        for child in element.children:
            if isinstance(child, Tag):
                extract_content(child, content_list)
    elif element.name == 'blockquote':
        for nested_child in element.children:
            if isinstance(nested_child, Tag):
                extract_content(nested_child, content_list)
    elif element.name == 'div' and element.find('pre'):
        content_list.append(element.text)



extract_header_context("https://twitter.com/Cx_SCS/status/1566438692805287941")