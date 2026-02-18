import os
import csv
import time
from multiprocessing import Pool, Manager, Lock
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initialize_driver(chromedriver_path):
    service = Service(executable_path=chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--enable-javascript")
    return webdriver.Chrome(service=service, options=options)


def write_text(content, filename, write_lock):
    folder = os.path.dirname(filename)
    with write_lock:
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(filename, "w", encoding="utf-8") as txtfile:
            txtfile.write(content)
            txtfile.flush()


def write_collected_pagelinks(data, collected_pagelinks_path, write_lock):
    timestamp, web, postdate, url = data
    with write_lock:
        folder = os.path.dirname(collected_pagelinks_path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(collected_pagelinks_path, "a", encoding="utf-8") as txtfile:
            txtfile.write(f"{timestamp}\t{web}\t{postdate}\t{url}\n")
            txtfile.flush()


def scroll_to_bottom(driver):
    initial_scroll_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.5)
        new_scroll_height = driver.execute_script("return document.body.scrollHeight")
        if new_scroll_height == initial_scroll_height:
            break
        initial_scroll_height = new_scroll_height


def parsetable(table_element):
    table_content = ""
    rows = table_element.find_all('tr')
    if not rows:
        return table_content
    for tr in rows:
        cells = tr.find_all(['th', 'td'])
        row = [cell.text.strip() for cell in cells]
        if row:
            table_content = table_content + '\n' + '\t'.join(row)
    return table_content


def parse_list_tags(list_tag):
    list_content = ""
    for li in list_tag.find_all('li', recursive=False):
        li_content = li.get_text().strip()
        nested_lists = li.find_all(['ul', 'ol'], recursive=False)
        for nested_list in nested_lists:
            li_content += '\n' + parse_list_tags(nested_list)
        list_content += '\n' + li_content
    return list_content


def parsecodes(page_element):
    codes = ""
    for code in page_element.find_all('code'):
        codes = codes + '\n' + code.text.strip()
    return codes


def process_iframe(medium_iframe_src, chromedriver_path):
    print(medium_iframe_src)
    table_data = ""
    try:
        driver_iframe = initialize_driver(chromedriver_path)
        driver_iframe.implicitly_wait(5)
        driver_iframe.get(medium_iframe_src)
        time.sleep(4)
        html = driver_iframe.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find_all('table')
        if table:
            for tr in table[0].find_all('tr'):
                row = '\t'.join(td.get_text().strip() for td in tr.find_all('td'))
                table_data += row + '\n'
    except Exception as e:
        print(f"Error processing iframe: {str(e)}")
    finally:
        driver_iframe.quit()
    return table_data


def parse_elements(driver, element, timestamp, chromedriver_path):
    page_content = ""
    processed_tags = set()

    def process_tag(tag):
        nonlocal page_content
        tag_id = id(tag)
        if tag_id in processed_tags:
            return
        processed_tags.add(tag_id)

        for br in tag.find_all("br"):
            br.replace_with("\n")

        if tag.name in ['p', 'code', 'h1', 'h2', 'h3']:
            tag_content = tag.get_text().strip()
            page_content += '\n' + tag_content

        elif tag.name == 'table':
            table_content = parsetable(tag)
            page_content += '\n' + table_content

        elif tag.name in ['ul', 'ol']:
            list_content = parse_list_tags(tag)
            page_content += '\n' + list_content

        elif tag.name == 'iframe':
            time.sleep(10)
            print(tag.get('src'))
            if tag.get('src'):
                iframe_src = tag.get('src')
                iframe_content = process_iframe(iframe_src, chromedriver_path)
                page_content += '\n' + iframe_content

        else:
            for child in tag.children:
                if isinstance(child, Tag):
                    process_tag(child)

    element_html = element.get_attribute('outerHTML')
    soup = BeautifulSoup(element_html, 'html.parser')

    for tag in soup.find_all(recursive=True):
        process_tag(tag)

    return page_content


def process_url(args):
    timestamp, postdate, page_url, web_name, base_paths = args
    chromedriver_path, text_dir, collected_pagelinks_path = base_paths

    driver = initialize_driver(chromedriver_path)
    try:
        print(f"Processing {page_url}")
        driver.get(page_url)
        time.sleep(3)
        filename = timestamp + ".txt"

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "hs_cos_wrapper_post_body"))
        )
        article_content = driver.find_element(By.ID, "hs_cos_wrapper_post_body")
        webpage_content = parse_elements(driver, article_content, timestamp, chromedriver_path)

        output_path = os.path.join(os.path.join(text_dir, web_name), filename)
        write_text(webpage_content, output_path, Lock())
        write_collected_pagelinks(
            (timestamp, web_name, postdate, page_url),
            collected_pagelinks_path,
            Lock()
        )
        print(f"Successfully processed {page_url}")

    except Exception as e:
        print(f"Error processing {page_url}: {str(e)}")
    finally:
        driver.quit()


class WebPageContent:

    def __init__(self, num_processes=4):
        current_dir = os.path.dirname(__file__)
        codes_dir = os.path.dirname(current_dir)
        project_dir = os.path.dirname(codes_dir)
        self.webpage_txt = os.path.join(current_dir, "pagelinks", "waiting_collection.txt")
        self.collected_pagelinks = os.path.join(current_dir, "pagelinks", "collected_pagelinks.txt")
        self.text_dir = os.path.join(project_dir, "Dataset", "NewContent")
        self.chromedriver = os.path.join(project_dir, "utils", "chromedriver", "macarm", "chromedriver")
        self.num_processes = num_processes

    def read_txt(self):
        webpage_dict = {}
        with open(self.webpage_txt) as txtfile:
            urlslist = txtfile.readlines()
            for url in urlslist:
                url_split = url.split("\t")
                timestamp = url_split[0].strip()
                source = url_split[1].strip()
                postdate = url_split[2].strip()
                page_url = url_split[3].strip()
                if source in webpage_dict:
                    webpage_dict[source].append((timestamp, postdate, page_url))
                else:
                    webpage_dict[source] = [(timestamp, postdate, page_url)]
        return webpage_dict

    def find_processed_files(self):
        processed_files = {}
        try:
            with open(self.collected_pagelinks) as txtfile:
                urlslist = txtfile.readlines()
                for url in urlslist:
                    url_split = url.split("\t")
                    timestamp = url_split[0].strip()
                    source = url_split[1].strip()
                    if source in processed_files:
                        processed_files[source].append(timestamp)
                    else:
                        processed_files[source] = [timestamp]
        except FileNotFoundError:
            pass
        return processed_files

    def sonatype_content(self):
        webpage_dict = self.read_txt()
        processed_files = self.find_processed_files()

        if "sonatype" not in webpage_dict:
            print("No sonatype URLs found")
            return

        base_paths = (self.chromedriver, self.text_dir, self.collected_pagelinks)

        urls = [
            (timestamp, postdate, page_url, "sonatype", base_paths)
            for timestamp, postdate, page_url in webpage_dict["sonatype"]
            if "sonatype" not in processed_files or
               timestamp not in processed_files["sonatype"]
        ]

        if not urls:
            print("All URLs have been processed")
            return

        with Pool(processes=self.num_processes) as pool:
            pool.map(process_url, urls)


if __name__ == '__main__':
    NUM_PROCESSES = 20
    webpage_content = WebPageContent(num_processes=NUM_PROCESSES)
    webpage_content.sonatype_content()
