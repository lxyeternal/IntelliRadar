# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : webpage_collection.py
# @Project  : PMonitor
# Time      : 22/1/24 9:33 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""

import re
import csv
import sys
import praw
csv.field_size_limit(sys.maxsize)
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from Configs.config import HEADER
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebPageCollection:
    def __init__(self):
        self.bleepingcomputer = "https://www.bleepingcomputer.com/tag/pypi/page/{}/"
        self.medium = "https://medium.com/checkmarx-security"
        self.sonatype = "https://blog.sonatype.com/page/{}"
        self.checkmarx = "https://checkmarx.com/blog/"
        self.socket = "https://socket.dev/blog"
        self.github = "https://github.com/advisories?page={}&query=type%3Amalware"
        self.jfrog = "https://jfrog.com/blog"
        self.datadoghq = "https://securitylabs.datadoghq.com/articles"
        self.qianxin = "https://tianwen.qianxin.com/blog/page/{}/"
        self.snyk = "https://snyk.io/blog/?tag=open-source-security&page={}"
        self.checkpoint = "https://research.checkpoint.com/intelligence-reports/page/{}/"
        self.old_webpage_txt = "pagelinks/old_time_webpage.txt"
        self.new_webpage_txt = "pagelinks/new_time_webpage.txt"
        self.old_webpage_dict = {}
        self.chromedriver = '../../utils/chromedriver/macarm/chromedriver'
        self.service = Service(executable_path=self.chromedriver)
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def load_old_webpages(self):
        for old_file in [self.old_webpage_txt, self.new_webpage_txt]:
            with open(old_file) as txtfile:
                urlslist = txtfile.readlines()
                for url in urlslist:
                    url_split = url.split("\t")
                    source = url_split[-3].strip()
                    page_url = url_split[-1].strip()
                    if source in self.old_webpage_dict:
                        self.old_webpage_dict[source].append(page_url)
                    else:
                        self.old_webpage_dict[source] = [page_url]

    def get_unique_timestamp(self):
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}"
        return filename


    def convert_date_format(self, date_string):
        try:
            try:
                date_obj = datetime.strptime(date_string, "%b %d, %Y")
            except:
                date_obj = datetime.strptime(date_string, "%B %d, %Y")
            # 格式化日期对象为所需的字符串格式
            formatted_date = date_obj.strftime("%Y-%m-%d")
            return formatted_date
        except (IndexError, ValueError):
            return "None"


    def write_txt(self, source, datetime, pageurl):
        timestamp = self.get_unique_timestamp()
        with open(self.new_webpage_txt, "a", encoding="utf-8") as txtfile:
            txtfile.write(timestamp + "\t" + source + "\t" + datetime + "\t" + pageurl + "\n")

    def bleepingcomputer_blog(self):
        for page_index in range(1, 4):
            if page_index == 1:
                pageurl = "https://www.bleepingcomputer.com/tag/npm/"
            else:
                pageurl = self.bleepingcomputer.format(page_index)
            self.driver.get(pageurl)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "bc-home-news-main-wrap")))
            self.driver.execute_script("window.stop();")  # 立即停止加载其余部分
            bc_latest_news = self.driver.find_element(By.ID, "bc-home-news-main-wrap")
            bc_latest_news_imgs = bc_latest_news.find_elements(By.CLASS_NAME, "bc_latest_news_text")
            for li_tag in bc_latest_news_imgs:
                li_url = li_tag.find_elements(By.TAG_NAME, "a")[1].get_attribute("href").strip()
                datetime_str = li_tag.find_element(By.CLASS_NAME, "bc_news_date").text.strip()
                formatted_date = self.convert_date_format(datetime_str.lower())
                if li_url not in self.old_webpage_dict.get("bleepingcomputer_pypi", []):
                    self.write_txt("bleepingcomputer_pypi", formatted_date, li_url)
                    print("bleepingcomputer_pypi", formatted_date, li_url)

    def medium_blog(self):
        self.driver.get(self.medium)
        # 模拟滚动到页面底部的JavaScript代码
        for _ in range(10):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        news_rows = self.driver.find_elements(By.CSS_SELECTOR, ".u-marginLeftNegative12.u-marginRightNegative12")
        for news_row in news_rows:
            news_divs = news_row.find_elements(By.CLASS_NAME, "u-marginBottom30")
            for news_div in news_divs:
                datetime_str = news_div.find_element(By.TAG_NAME, "time").get_attribute("datetime").strip()
                news_href = news_div.find_element(By.TAG_NAME, "a").get_attribute("href")
                news_href = news_href.split("?source")[0].strip()
                if news_href not in self.old_webpage_dict.get("medium", []):
                    self.write_txt("medium", datetime_str, news_href)
                    print("medium", datetime_str, news_href)

    def medium_recommand(self):
        page_url = "https://medium.com/tag/supply-chain-security/recommended"
        self.driver.get(page_url)
        self.driver.implicitly_wait(10)
        for count in range(50):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        news_blogs = self.driver.find_elements(By.CSS_SELECTOR, ".bg.jd.je.jf.jg")
        for news_blog in news_blogs:
            news_url_div = news_blog.find_element(By.CSS_SELECTOR, ".l.er.ju")
            news_url = news_url_div.find_element(By.TAG_NAME, "a").get_attribute("href").strip().split("?source")[
                0].strip()
            datetime_str = news_blog.find_element(By.CSS_SELECTOR, ".lg.lh.li.lj.lk.ab.q").text.strip()
            datetime_str_split = datetime_str.split("·")[-1].strip().lower()
            if "days ago" in datetime_str_split or "day ago" in datetime_str_split:
                current_date = datetime.now()
                # 解析出天数
                days_ago = int(datetime_str_split.split()[0])
                # 计算具体日期
                specific_date = current_date - timedelta(days=days_ago)
                # 格式化日期
                formatted_date = specific_date.strftime('%Y-%m-%d')
            else:
                formatted_date = self.convert_date_format(datetime_str_split)
            if news_url not in self.old_webpage_dict.get("medium_recommand", []):
                self.write_txt("medium_recommand", formatted_date, news_url)
                print("medium_recommand", formatted_date, news_url)


    def sonatype_blog(self):
        for page_index in range(110):
            page_url = self.sonatype.format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            blog_section = soup.find_all(class_='blog-section')[1]
            row_fluids = blog_section.find_all(class_='row-fluid')
            for row_fluid in row_fluids:
                listing_boxs = row_fluid.find_all("div", class_="span4 listing-box")
                for listing_box in listing_boxs:
                    boxs_behind = listing_box.find(class_="behind")
                    a_tag = boxs_behind.find('a', class_='hs-featured-image-link')
                    datetime_str = listing_box.find("div", class_="hubspot-editable").text.strip()
                    date_pattern = r"\b(\w+)\s+(\d{1,2}),\s+(\d{4})\b"
                    match = re.search(date_pattern, datetime_str)
                    formatted_date = "None"
                    if match:
                        # 提取年、月、日
                        month = match.group(1)
                        day = match.group(2)
                        year = match.group(3)
                        # 构建日期字符串
                        date_string = f"{month} {day}, {year}".lower()
                        formatted_date = self.convert_date_format(date_string)
                    if a_tag:
                        href_value = a_tag.get('href')
                        if href_value not in self.old_webpage_dict.get("sonatype", []):
                            self.write_txt("sonatype", formatted_date, href_value)
                            print("sonatype", formatted_date, href_value)
                    else:
                        pass

    def sonatype_oss_blog(self):
        blog_url = "https://blog.sonatype.com/topic/everything-open-source/page/{}"
        for page_index in range(12):
            page_url = blog_url.format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            blog_section = soup.find_all(class_='blog-section')[1]
            row_fluids = blog_section.find_all(class_='row-fluid')
            for row_fluid in row_fluids:
                listing_boxs = row_fluid.find_all("div", class_="span4 listing-box")
                for listing_box in listing_boxs:
                    boxs_behind = listing_box.find(class_="behind")
                    a_tag = boxs_behind.find('a', class_='hs-featured-image-link')
                    datetime_str = listing_box.find("div", class_="hubspot-editable").text.strip()
                    date_pattern = r"\b(\w+)\s+(\d{1,2}),\s+(\d{4})\b"
                    match = re.search(date_pattern, datetime_str)
                    formatted_date = "None"
                    if match:
                        # 提取年、月、日
                        month = match.group(1)
                        day = match.group(2)
                        year = match.group(3)
                        # 构建日期字符串
                        date_string = f"{month} {day}, {year}".lower()
                        formatted_date = self.convert_date_format(date_string)
                    if a_tag:
                        href_value = a_tag.get('href').strip()
                        if href_value not in self.old_webpage_dict.get("sonatype_oss", []):
                            self.write_txt("sonatype_oss", formatted_date, href_value)
                            print("sonatype_oss", formatted_date, href_value)
                    else:
                        pass

    def checkmarx_blog(self):
        self.driver.get(self.checkmarx)
        # 模拟滚动到页面底部的JavaScript代码
        for _ in range(21):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        time.sleep(5)
        news_block = self.driver.find_element(By.CSS_SELECTOR, ".premium-blog-wrap.premium-blog-even")
        premium_blog_posts = news_block.find_elements(By.CSS_SELECTOR, ".premium-blog-post-outer-container")
        for premium_blog_post in premium_blog_posts:
            premium_blog_entry_title = premium_blog_post.find_element(By.CLASS_NAME, "premium-blog-entry-title")
            news_href = premium_blog_entry_title.find_element(By.TAG_NAME, "a").get_attribute("href").strip()
            datetime_str = premium_blog_post.find_element(By.CLASS_NAME, "premium-blog-entry-meta").text.strip().lower()
            formatted_date = self.convert_date_format(datetime_str)
            if news_href not in self.old_webpage_dict.get("checkmarx", []):
                self.write_txt("checkmarx", formatted_date, news_href)
                print("checkmarx", formatted_date, news_href)


    def socket_blog(self):
        response = requests.get(self.socket, headers=HEADER)
        soup = BeautifulSoup(response.text, 'html.parser')
        css_vql929 = soup.find("div", class_="css-1vql929")
        chakra_linkbox = css_vql929.find_all("article", class_="chakra-linkbox")
        for linkbox in chakra_linkbox:
            css_rqbta = linkbox.find("div", class_="css-rqbta8")
            date_str = css_rqbta.find_all("span")[-1].text.strip().replace("-", "").strip().lower()
            formatted_date = self.convert_date_format(date_str)
            chakra_heading = linkbox.find("h3", class_="chakra-heading")
            href_div = chakra_heading.find("a", class_="chakra-linkbox__overlay")
            href_value = href_div.get('href')
            full_link = "https://socket.dev" + href_value
            if full_link not in self.old_webpage_dict.get("socket", []):
                self.write_txt("socket", formatted_date, full_link)
                print("socket", formatted_date, full_link)


    def github_blog(self):
        for page_index in range(1, 50):
            page_url = self.github.format(page_index)
            self.driver.get(page_url)
            time.sleep(5)
            self.driver.implicitly_wait(10)
            navigation_container = self.driver.find_element(By.CLASS_NAME, "js-active-navigation-container")
            navigation_items = navigation_container.find_elements(By.CLASS_NAME, "js-navigation-item")
            for navigation_item in navigation_items:
                datetime = navigation_item.find_element(By.TAG_NAME, "relative-time").get_attribute("datetime")
                href_value = navigation_item.find_element(By.TAG_NAME, "a").get_attribute("href")
                if href_value not in self.old_webpage_dict.get("github", []):
                    self.write_txt("github", datetime, href_value)
                    print("github", datetime, href_value)


    def jfrog_blog(self):
        self.driver.get(self.jfrog)
        self.driver.implicitly_wait(10)
        posts_wrap = self.driver.find_element(By.CLASS_NAME, "posts-wrap")
        blog_posts = posts_wrap.find_elements(By.CSS_SELECTOR, ".col-md-6.blog-post-title")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        while True:
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # 查找"Next"按钮并等待它可点击
                next_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "next")))
                # 将页面滚动到"Next"按钮所在的位置
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                # 尝试使用JavaScript触发点击事件
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(10)
                # 等待新页面加载完成
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "posts-wrap")))
                posts_wrap = self.driver.find_element(By.CLASS_NAME, "posts-wrap")
                blog_posts = posts_wrap.find_elements(By.CSS_SELECTOR, ".col-md-6.blog-post-title")
                for blog_post in blog_posts:
                    post_date = blog_post.find_element(By.CLASS_NAME, "blog-post-date").text.split()[:3]
                    date_str = ' '.join(post_date).lower()
                    formatted_date = self.convert_date_format(date_str)
                    blog_post_link = blog_post.find_element(By.TAG_NAME, "a").get_attribute("href")
                    if blog_post_link not in self.old_webpage_dict.get("jfrog", []):
                        self.write_txt("jfrog", formatted_date, blog_post_link)
                        print("jfrog", formatted_date, blog_post_link)
            except NoSuchElementException:
                print("找不到'Next'按钮,可能已到达最后一页")
                break
            except Exception as e:
                print(f"发生错误: {str(e)}")
                break


    def datadoghq_blog(self):
        self.driver.get(self.datadoghq)
        while True:
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ais-InfiniteHits-loadMore")))
                more_button = self.driver.find_element(By.CLASS_NAME, "ais-InfiniteHits-loadMore")
                more_button.click()
                self.driver.implicitly_wait(5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except:
                break
        time.sleep(2)
        InfiniteHits_item = self.driver.find_elements(By.CLASS_NAME, "ais-InfiniteHits-item")
        for item in InfiniteHits_item:
            datetime_str = item.find_elements(By.CLASS_NAME, "hit-header-text")[1].text.strip().lower()
            formatted_date = self.convert_date_format(datetime_str)
            hit_title = item.find_element(By.CLASS_NAME, "hit-title-link").get_attribute("href")
            if hit_title not in self.old_webpage_dict.get("datadoghq", []):
                self.write_txt("datadoghq", formatted_date, hit_title)
                print("datadoghq", formatted_date, hit_title)


    def qianxin_blog(self):
        for page_index in range(1, 13):
            if page_index == 1:
                page_url = "https://tianwen.qianxin.com/blog/"
            else:
                page_url = self.qianxin.format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            recent_post_items = soup.find_all("article", class_="recent-post-item")
            for item in recent_post_items:
                formatted_date = item.find('time', class_='time').get('datetime')
                href_value = item.find("a", class_="title").get('href')
                full_link = "https://tianwen.qianxin.com" + href_value
                if full_link not in self.old_webpage_dict.get("qianxin", []):
                    self.write_txt("qianxin", formatted_date, full_link)
                    print("qianxin", formatted_date, full_link)


    def snyk_blog(self):
        for page_index in range(1, 29):
            page_url = self.snyk.format(page_index)
            resource = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(resource.text, 'html.parser')
            news_blogs = soup.find_all("div", class_="w-full marg-h-auto p-relative h-full")
            for news_blog in news_blogs:
                datetime_str = news_blog.find("p", class_="txt-body txt-color-body txt-line-clamp-4").text.strip().lower()
                formatted_date = self.convert_date_format(datetime_str)
                news_href = news_blog.find("a", class_="group txt-decoration-none").get('href')
                full_link = "https://snyk.io" + news_href
                if full_link not in self.old_webpage_dict.get("snyk", []):
                    self.write_txt("snyk", formatted_date, full_link)
                    print("snyk", formatted_date, full_link)

    def securityaffairs_blog(self):
        for page_index in range(1, 3):
            page_url = "https://securityaffairs.com/tag/pypi/page/{}".format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            latest_news_block = soup.find("div", class_="latest-news-block")
            article_rows = latest_news_block.find_all("div", class_="news-card news-card-category mb-3 mb-lg-5")
            for article in article_rows:
                post_time = article.find("div", class_="post-time mb-3")
                datetime_str = post_time.find_all("span")[1].text.strip().lower()
                formatted_date = self.convert_date_format(datetime_str)
                article_link = article.find("a").get('href')
                if article_link not in self.old_webpage_dict.get("securityaffairs", []):
                    self.write_txt("securityaffairs", formatted_date, article_link)
                    print("securityaffairs", formatted_date, article_link)


    def fortinet_blog(self):
        self.driver.get("https://www.fortinet.com/blog/threat-research")
        flag = 30
        while flag:
            flag -= 1
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "b3-blog-list__pagination")))
                more_button = self.driver.find_element(By.CLASS_NAME, "btn")
                more_button.click()
                self.driver.implicitly_wait(5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except:
                break
        time.sleep(2)
        InfiniteHits_item = self.driver.find_elements(By.CSS_SELECTOR, ".b3-blog-list__post.text-container")
        for item in InfiniteHits_item:
            hit_title = item.find_element(By.CLASS_NAME, "b3-blog-list__background").find_element(By.TAG_NAME, "a").get_attribute("href")
            b3_blog_list__meta = item.find_element(By.CLASS_NAME, "b3-blog-list__meta")
            datetime_str = b3_blog_list__meta.find_elements(By.TAG_NAME, "span")[1].text.strip().lower()
            formatted_date = self.convert_date_format(datetime_str)
            if hit_title not in self.old_webpage_dict.get("fortinet", []):
                self.write_txt("fortinet", formatted_date, hit_title)
                print("fortinet", formatted_date, hit_title)


    def phylum_blog(self):
        for page_index in range(1, 22):
            page_url = "https://blog.phylum.io/page/{}/".format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            latest_news_block = soup.find_all("article", class_=["post tag-research", "post tag-insights", "post tag-research featured"])
            for article in latest_news_block[1:]:
                article_link = article.find("a", class_="post-title-link").get('href')
                formatted_date = article.find("time").get('datetime')
                full_link = "https://blog.phylum.io" + article_link
                if full_link not in self.old_webpage_dict.get("phylum", []):
                    self.write_txt("phylum", formatted_date, full_link)
                    print("phylum", formatted_date, full_link)


    def reversinglabs_blog(self):
        for page_index in range(1, 21):
            page_url = "https://www.reversinglabs.com/blog/tag/appsec-supply-chain-security/page/{}/".format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            blog__listing_item = soup.find("div", class_="blog__listing-item")
            article_rows = blog__listing_item.find_all("article", class_="blog__item")
            for article in article_rows:
                datetime_str = article.find("time").get('datetime')
                article_link = article.find("a").get('href')
                if article_link not in self.old_webpage_dict.get("reversinglabs", []):
                    self.write_txt("reversinglabs", datetime_str, article_link)
                    print("reversinglabs", datetime_str, article_link)


    def tuxcare_blog(self):
        self.driver.get("https://tuxcare.com/blog/")
        time.sleep(2)
        InfiniteHits_item = self.driver.find_element(By.CLASS_NAME, "blog-posts")
        posts = InfiniteHits_item.find_elements(By.CLASS_NAME, "post")
        for item in posts:
            hit_title = item.find_element(By.TAG_NAME, "a").get_attribute("href")
            post_date_element = item.find_element(By.CLASS_NAME, "post-date").find_element(By.TAG_NAME, "span")
            datetime_str = post_date_element.get_attribute('outerHTML').replace('<span>', '').replace('</span>', '')
            date_obj = datetime.strptime(datetime_str, "%B %d, %Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            if hit_title not in self.old_webpage_dict.get("tuxcare", []):
                self.write_txt("tuxcare", formatted_date, hit_title)
                print("tuxcare", formatted_date, hit_title)


    def twitter_blog(self):
        link_list = set()
        with open("../../csv/google_source.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                url_link = row[4]
                if "twitter.com" in url_link:
                    link_list.add(url_link)
        for link in link_list:
            self.write_txt("twitter", link)
            print(link)


    def cybersecuritynews_blog(self):
        for page_index in range(1, 6):
            page_url = "https://cybersecuritynews.com/page/{}/?s=npm".format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            latest_news_block = soup.find_all("div", class_="td_module_16 td_module_wrap td-animation-stack")
            for article in latest_news_block:
                post_date = article.find("span", class_="td-post-date").find("time").get('datetime')
                article_link = article.find("a").get('href')
                if article_link not in self.old_webpage_dict.get("cybersecuritynews", []):
                    self.write_txt("cybersecuritynews", post_date, article_link)
                    print("cybersecuritynews", post_date, article_link)

    def rhisac_blog(self):
        for page_index in range(1, 79):
            page_url = "https://rhisac.org/blog/page/{}/".format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            latest_news_block = soup.find_all("article", class_="post inner-row")
            for article in latest_news_block:
                article_link = article.find("a").get('href').strip()
                datetime_text = article.find("p", class_="mb-0").text.strip()
                formatted_date = self.convert_date_format(datetime_text)
                if article_link not in self.old_webpage_dict.get("rhisac", []):
                    self.write_txt("rhisac", formatted_date, article_link)
                    print("rhisac", formatted_date, article_link)



    def checkpoint_blog(self):
        for page_index in range(1, 76):
            page_url = self.checkpoint.format(page_index)
            response = requests.get(page_url, headers=HEADER)
            soup = BeautifulSoup(response.text, 'html.parser')
            latest_news_block = soup.find_all("div", class_="box col-margin relative border-dotted")
            for article in latest_news_block:
                post_date = article.find("div", class_="date small-font").text.strip()
                formatted_date = self.convert_date_format(post_date)
                article_link = article.find("a").get('href')
                if article_link not in self.old_webpage_dict.get("checkpoint", []):
                    print("checkpoint", formatted_date, article_link)
                    self.write_txt("checkpoint", formatted_date, article_link)


    def reddit_blog(self):
        self.client_id = 'iV-ef53EmAfBoz5AkekvQw'
        self.client_secret = 'IpiY_5kH56aH9ZNcnZSr889n0czZ3w'
        self.username = 'iBlueair'
        self.password = 'guowenbo1011'
        # 初始化 praw 实例
        self.reddit = praw.Reddit(
            client_id=self.client_id,  # 替换为你的客户端ID
            client_secret=self.client_secret,  # 替换为你的客户端密钥
            user_agent='SCC'  # 替换为你的用户代理字符串
        )
        with open("/Users/blue/Documents/GitHub/SCC_Intelligence/codes/Collection/pagelinks/malicious-Reddit-Search.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                url_link = row[1].strip()
                try:
                    submission = self.reddit.submission(url=url_link)
                    # 打印帖子的创建时间
                    created_time = datetime.utcfromtimestamp(submission.created_utc)
                    formatted_date = created_time.strftime('%Y-%m-%d')
                    print(formatted_date)  # 格式化日期时间
                except:
                    formatted_date = "None"
                self.write_txt("reddit", formatted_date, url_link)



if __name__ == '__main__':
    webpagecollection = WebPageCollection()
    webpagecollection.load_old_webpages()
    # webpagecollection.snyk_blog()
    # webpagecollection.qianxin_blog()
    # webpagecollection.datadoghq_blog()
    # webpagecollection.jfrog_blog()
    # webpagecollection.github_blog()
    # webpagecollection.medium_recommand()
    # webpagecollection.medium_blog()
    # webpagecollection.checkmarx_blog()
    # webpagecollection.sonatype_oss_blog()
    # webpagecollection.sonatype_blog()
    # webpagecollection.bleepingcomputer_blog()
    # webpagecollection.securityaffairs_blog()
    # webpagecollection.fortinet_blog()
    # webpagecollection.phylum_blog()
    # webpagecollection.reversinglabs_blog()
    # webpagecollection.tuxcare_blog()
    # webpagecollection.twitter_blog()
    # webpagecollection.cybersecuritynews_blog()
    # webpagecollection.rhisac_blog()
    # webpagecollection.socket_blog()
    webpagecollection.checkpoint_blog()
    # webpagecollection.reddit_blog()