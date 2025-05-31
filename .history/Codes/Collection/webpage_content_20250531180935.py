# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : webpage_content.py
# @Project  : PMonitor
# Time      : 25/1/24 9:58 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


import os
import csv
import time
import praw
import subprocess
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WebPageContent:
    def __init__(self):
        self.current_dir = os.path.dirname(__file__)
        self.codes_dir = os.path.dirname(self.current_dir)
        self.project_dir = os.path.dirname(self.codes_dir)
        self.webpage_dict = {}
        self.processed_files = []
        self.text_dir = os.path.join(self.project_dir, "Dataset/Content/")
        self.webpage_txt = os.path.join(self.codes_dir, "Collection/pagelinks/collected_pagelinks.txt")
        self.chromedriver = os.path.join(self.project_dir, "utils/chromedriver/macarm/chromedriver")
        self.service = Service(executable_path=self.chromedriver)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--enable-javascript")

    def write_text(self, content, filepath):
        # Get the folder path
        folder = os.path.dirname(filepath)
        # Create the folder if it doesn't exist
        if not os.path.exists(folder):
            os.makedirs(folder)
        # Now we can safely write to the file
        with open(filepath, "a", encoding="utf-8") as txtfile:
            txtfile.write(content)
            txtfile.flush()

    def write_csv(self, data):
        with open((os.path.join(self.project_dir, "Dataset/CSV/Github_data.csv")), "a") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(data)
            # write data to the csv file right now
            csvfile.flush()

    def find_processed_files(self, file_dir):
        for root, dirs, files in os.walk(file_dir):
            for file in files:
                self.processed_files.append(file)

    def scroll_to_bottom(self, driver):
        # Initialize the height before scrolling
        initial_scroll_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll a small portion each time
            driver.execute_script("window.scrollBy(0, 300);")
            # Wait for the page to load new content (if any)
            time.sleep(0.5)
            # Check if we've reached the bottom of the page
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if new_scroll_height == initial_scroll_height:
                break
            initial_scroll_height = new_scroll_height

    def parsetable(self, table_element):
        # Extract table headers
        table_content = ""
        header_row = table_element.find('tr')
        headers = [th.text.strip() for th in header_row.find_all('th')]
        table_content = table_content + '\n' + '\t'.join(headers)
        # Extract each row of the table
        for tr in table_element.find_all('tr')[1:]:  # Skip the header row
            row = [td.text.strip() for td in tr.find_all('td')]
            table_content = table_content + '\n' + '\t'.join(row)
        return table_content


    def parse_list_tags(self, list_tag):
        list_content = ""
        for li in list_tag.find_all('li', recursive=False):
            # For each li element, extract the text
            # If the li element contains ul or ol, recursively call parse_list_tags
            li_content = li.get_text().strip()
            nested_lists = li.find_all(['ul', 'ol'], recursive=False)
            for nested_list in nested_lists:
                li_content += '\n' + self.parse_list_tags(nested_list)
            list_content += '\n' + li_content
        return list_content


    def parsecodes(self, page_element):
        codes = ""
        for code in page_element.find_all('code'):
            codes = codes + '\n' + code.text.strip()
        return codes


    def extract_body(self, doc):
        page_content = ""
        if doc.summary().startswith("<html>"):
            soup = BeautifulSoup(doc.summary(), "html.parser")
            for tag in soup.find_all(recursive=False):  # True makes find_all return all tags
                if tag.name == "table":
                    table_content = self.parsetable(tag)
                    page_content = page_content + '\n' + table_content
                else:
                    page_content = page_content + '\n' + tag.text.strip()
        else:
            page_content = doc.summary()
        return page_content


    def process_iframe(self, medium_iframe_src):
        table_data = ""
        try:
            driver_iframe = webdriver.Chrome(service=self.service, options=self.options)
            driver_iframe.implicitly_wait(5)
            driver_iframe.get(medium_iframe_src)
            time.sleep(2)
            html = driver_iframe.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find_all('table')
            for tr in table[0].find_all('tr'):
                # Extract each row's cells and join with '\t'
                row = '\t'.join(td.get_text().strip() for td in tr.find_all('td'))
                table_data += row + '\n'
        except:
            pass
        return table_data


    def parse_elements(self, driver, element):
        page_content = ""
        processed_tags = set()  # For tracking already processed tags
        def process_tag(tag):
            nonlocal page_content
            if tag in processed_tags:
                return
            processed_tags.add(tag)
            for br in tag.find_all("br"):
                br.replace_with("\n")
            # Apply specific processing functions to specific tags
            if tag.name in ['p', 'code', 'h1', 'h2', 'h3']:
                # Replace <br> tags with newlines
                tag_content = tag.get_text().strip()
                page_content += '\n' + tag_content
                return  # Skip child tags of these tags
            elif tag.name == 'table':
                table_content = self.parsetable(tag)
                page_content += '\n' + table_content
                return
            elif tag.name in ['ul', 'ol']:
                list_content = self.parse_list_tags(tag)
                page_content += '\n' + list_content
                return
            elif tag.name == 'iframe':
                iframe_src = tag['src']
                iframe_content = self.process_iframe(iframe_src)
                page_content += '\n' + iframe_content
                with open("iframe.txt", "a") as txtfile:
                    txtfile.write(iframe_content)
                    txtfile.write("\n")
                return
            else:
                # If the tag is not a specific tag, traverse its child tags
                if tag.children:
                    for child in tag.children:
                        if isinstance(child, Tag):  # Ensure the child element is a tag
                            process_tag(child)
                else:
                    # If the tag has no child tags, directly extract its text
                    tag_content = tag.get_text().strip()
                    page_content += '\n' + tag_content

        children = element.find_elements(By.XPATH, "./*")
        for child in children:
            if child.tag_name.lower() == "iframe":
                iframe_src = child.get_attribute('src')
                iframe_content = self.process_iframe(iframe_src)
                page_content += iframe_content
                with open("iframe.txt", "a") as txtfile:
                    txtfile.write(iframe_content)
                    txtfile.write("\n")
            else:
                child_html = child.get_attribute('outerHTML')
                child_soup = BeautifulSoup(child_html, 'html.parser')
                # Only process top-level tags
                for tag in child_soup.children:
                    if tag.name:  # Ensure it's a BeautifulSoup tag
                        process_tag(tag)
        return page_content


    def print_all_child_tags(self, element):
        # Recursively traverse all child elements
        children = element.find_elements(By.XPATH, "./*")
        for child in children:
            self.print_all_child_tags(child)

    def medium_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        count = 0
        try:
            filename = timestamp + ".txt"
            count += 1
            driver.get(webpage_link)
            # Define JavaScript script for smooth scrolling
            smooth_scroll_script = """
            let intervalId = setInterval(function() {
                window.scrollBy(0, 200); // Scroll down 200 pixels each time
            }, 100); // Scroll every 100 milliseconds

            // Set a timeout to prevent infinite scrolling
            setTimeout(function() {
                clearInterval(intervalId);
            }, 15000); // Stop scrolling after 15 seconds
            """
            # Execute JavaScript script
            driver.execute_script(smooth_scroll_script)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(20)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ch.bg.fy.fz.ga.gb")))
            content_div = driver.find_elements(By.CSS_SELECTOR, ".ch.bg.fy.fz.ga.gb")[1]
            page_content = self.parse_elements(driver, content_div)
            self.write_text(page_content, os.path.join(os.path.join(self.text_dir, "medium"), filename))
        except:
            print("------Error-------")

    def qianxin_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        try:
            driver.get(webpage_link)
            filename = timestamp + ".txt"
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post-content")))
            post_content = driver.find_element(By.CLASS_NAME, "post-content")
            # Recursively traverse all tags in article_content until there are no child tags. If the child tag is a p, code, h1, h2, or h3 tag, output the content of the tag. If it's a table tag, it needs to be processed separately to restore the content and format of the table. But note that after parsing the content of a tag, we need to skip this tag to prevent duplicate output
            webpage_content = self.parse_elements(driver, post_content)
            # print(webpage_content)
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "qianxin"), filename))
        except:
            pass


    def snyk_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        filename = timestamp + ".txt"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "txt-rich-long")))
        article_content = driver.find_element(By.CLASS_NAME, "txt-rich-long")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "snyk"), filename))


    def github_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        article_main = driver.find_element(By.TAG_NAME, "main")
        Subhead_description = article_main.find_element(By.CLASS_NAME, "Subhead-description")
        v_align_middle = Subhead_description.find_element(By.CLASS_NAME, "v-align-middle").text.strip()
        datatime = Subhead_description.find_element(By.TAG_NAME, "relative-time").get_attribute("datetime")
        table_content = article_main.find_element(By.CSS_SELECTOR, ".gutter-lg.gutter-condensed.clearfix")
        name_manager = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-12.col-md-6.pr-md-2")
        package_name = name_manager.find_element(By.CSS_SELECTOR, ".f4.color-fg-default.text-bold").text.strip()
        manager_name = name_manager.find_element(By.CSS_SELECTOR, ".color-fg-muted.f4.d-inline-flex").text
        manager_name = manager_name.replace("(", "").replace(")", "").strip()
        version_div = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-6.col-md-3.py-2.py-md-0.pr-2")
        version = version_div.find_element(By.CSS_SELECTOR, ".f4.color-fg-default").text.strip()
        description_div = table_content.find_element(By.CSS_SELECTOR, ".Box-body.px-5.pb-5")
        description = description_div.text
        right_table = article_main.find_element(By.CSS_SELECTOR, ".col-12.col-md-3.float-left.pt-3.pt-md-0")
        weakness = right_table.find_element(By.CSS_SELECTOR, ".discussion-sidebar-item.js-repository-advisory-details").text.strip()
        self.write_csv([v_align_middle, datatime, package_name, manager_name, version, description, weakness])
        driver.quit()


    def bleepingcomputer_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(10)
        filename = timestamp + ".txt"
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "article-section")))
            # driver.execute_script("window.stop();")  # 立即停止加载其余部分
        except:
            article_section = driver.find_element(By.CLASS_NAME, "article-section")
            webpage_content = self.parse_elements(driver, article_section)
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "bleepingcomputer"), filename))


    def jfrog_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(5)
        filename = timestamp + ".txt"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        article_section = driver.find_element(By.CLASS_NAME, "entry-content")
        webpage_content = self.parse_elements(driver, article_section)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "jfrog"), filename))


    def sonatype_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        filename = timestamp + ".txt"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "hs_cos_wrapper_post_body")))
        article_content = driver.find_element(By.ID, "hs_cos_wrapper_post_body")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "sonatype"), filename))


    def checkmarx_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        filename = timestamp + ".txt"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".elementor-element.elementor-element-2bd10d61.elementor-widget.elementor-widget-theme-post-content")))
            article_content = driver.find_element(By.CSS_SELECTOR, ".elementor-element.elementor-element-2bd10d61.elementor-widget.elementor-widget-theme-post-content")
            webpage_content = self.parse_elements(driver, article_content)
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "checkmarx"), filename))
        except:
            pass

    def datadoghq_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        filename = timestamp + ".txt"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".article-content.relative")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".article-content.relative")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "datadoghq"), filename))


    def socket_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".prose.css-0")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".prose.css-0")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "socket"), timestamp + ".txt"))

    def twitter_content(self, timestamp, webpage_link):
        usernames = ["@machycek"]
        # 循环遍历用户名列表
        for username in usernames:
            # 构建命令
            command = ['python', './twitter-scraper/scraper', '--tweets=800', f'--username={username}']
            try:
                print(f"正在为 {username} 执行命令...")
                result = subprocess.run(command, check=True, text=True, capture_output=True)
                print(f"{username} 命令输出：", result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"{username} 命令执行发生错误：", e.stderr)
            print(f"{username} 命令执行完成。\n")
        # 所有命令执行完毕
        print("所有命令执行完毕。")

    def rhisac_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".elementor-widget.elementor-widget-theme-post-content")))
        elementor_widget = driver.find_element(By.CSS_SELECTOR, ".elementor-widget.elementor-widget-theme-post-content")
        article_content = elementor_widget.find_element(By.CLASS_NAME, "elementor-widget-container")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "rhisac"), timestamp + ".txt"))

    def cybersecuritynews_content(self, timestamp, webpage_link):
        self.find_processed_files(os.path.join(self.text_dir, "cybersecuritynews"))
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        try:
            driver.get(webpage_link)
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".td-post-content.tagdiv-type")))
            article_content = driver.find_element(By.CSS_SELECTOR, ".td-post-content.tagdiv-type")
            webpage_content = self.parse_elements(driver, article_content)
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "cybersecuritynews"), filename))
        except:
            self.write_text("", os.path.join(os.path.join(self.text_dir, "cybersecuritynews"), filename))

    def tuxcare_content(self, timestamp, webpage_link):
        self.find_processed_files(os.path.join(self.text_dir, "tuxcare"))
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        try:
            driver.get(webpage_link)
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tcl-m-content")))
            article_content = driver.find_element(By.CLASS_NAME, "tcl-m-content")
            webpage_content = self.parse_elements(driver, article_content)
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "tuxcare"), filename))
        except:
            self.write_text("", os.path.join(os.path.join(self.text_dir, "tuxcare"), filename))


    def reversinglabs_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "hs_cos_wrapper_post_body")))
        article_content = driver.find_element(By.ID, "hs_cos_wrapper_post_body")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "reversinglabs"), filename))


    def fortinet_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".aem-Grid.aem-Grid--12.aem-Grid--default--12")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".aem-Grid.aem-Grid--12.aem-Grid--default--12")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "fortinet"), filename))


    def securityaffairs_content(self, timestamp, webpage_link):
        self.find_processed_files(os.path.join(self.text_dir, "securityaffairs"))
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".article-details-block.wow.fadeInUp.animated")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".article-details-block.wow.fadeInUp.animated")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "securityaffairs"), filename))


    def phylum_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gh-content.gh-canvas")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".gh-content.gh-canvas")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "phylum"), filename))


    def checkpoint_content(self, timestamp, webpage_link):
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        filename = timestamp + ".txt"
        driver.get(webpage_link)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".text.border-bottom")))
        article_content = driver.find_element(By.CSS_SELECTOR, ".text.border-bottom")
        webpage_content = self.parse_elements(driver, article_content)
        self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "checkpoint"), filename))


    def reddit_content(self, timestamp, webpage_link):
        self.client_id = 'iV-ef53EmAfBoz5AkekvQw'
        self.client_secret = 'IpiY_5kH56aH9ZNcnZSr889n0czZ3w'
        self.username = 'iBlueair'
        self.password = 'guowenbo1011'
        # Initialize praw instance
        self.reddit = praw.Reddit(
            client_id=self.client_id,  # Replace with your client ID
            client_secret=self.client_secret,  # Replace with your client secret
            user_agent='SCC'  # Replace with your user agent string
        )
        self.find_processed_files(os.path.join(self.text_dir, "reddit"))
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.implicitly_wait(5)
        for timestamp, page_url in self.webpage_dict["reddit"]:
            filename = timestamp + ".txt"
            if filename in self.processed_files:
                continue
            webpage_content = ""
            submission = self.reddit.submission(url=page_url)
            # Print the title and content of the post
            webpage_content += submission.title + '\n' + submission.selftext + '\n'
            submission.comments.replace_more(limit=50)
            for comment in submission.comments.list():
                # Print the content of the comment
                webpage_content += comment.body + '\n'
            self.write_text(webpage_content, os.path.join(os.path.join(self.text_dir, "reddit"), filename))


# if __name__ == '__main__':
#     webpage_content = WebPageContent()
#     timestamp = "2021-08-24"
#     webpage_link = "https://www.reddit.com/r/netsec/comments/p9zv3v/this_week_in_security_news_20210820/"
#     webpage_content.datadoghq_content(timestamp, webpage_link)
#     webpage_content.snyk_content()
#     webpage_content.qianxin_content()
#     webpage_content.jfrog_content()
#     webpage_content.github_content()
#     webpage_content.medium_content()
#     webpage_content.checkmarx_content()
#     webpage_content.sonatype_content()
#     webpage_content.bleepingcomputer_content()
#     webpage_content.securityaffairs_content()
#     webpage_content.fortinet_content()
#     webpage_content.phylum_content()
#     webpage_content.reversinglabs_content()
#     webpage_content.tuxcare_content()
#     webpage_content.twitter_content()
#     webpage_content.cybersecuritynews_content()
#     webpage_content.rhisac_content()
#     webpage_content.socket_content()
#     webpage_content.checkpoint_content()
#     webpage_content.reddit_content()
