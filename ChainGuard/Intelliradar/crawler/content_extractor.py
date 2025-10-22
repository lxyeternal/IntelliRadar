"""
Content extraction utilities for web crawlers
Extracted from the old webpage_content.py to provide reusable content extraction functionality
"""

import os
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag


class ContentExtractor:
    """Base class for content extraction using Selenium and BeautifulSoup"""
    
    def __init__(self):
        # Get the current directory and construct path to chromedriver
        current_dir = os.path.dirname(__file__)
        intelliradar_dir = os.path.dirname(current_dir)
        chromedriver_path = os.path.join(intelliradar_dir, "drivers/linux/chromedriver")
        
        # Use local chromedriver with executable_path parameter
        self.service = Service(executable_path=chromedriver_path)
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-web-security")
        self.options.add_argument("--allow-running-insecure-content")
        
    def get_driver(self) -> webdriver.Chrome:
        """Get a new Chrome WebDriver instance"""
        return webdriver.Chrome(service=self.service, options=self.options)
    
    def scroll_to_bottom(self, driver: webdriver.Chrome):
        """Scroll to bottom of page to load dynamic content"""
        initial_scroll_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(0.5)
            new_scroll_height = driver.execute_script("return document.body.scrollHeight")
            if new_scroll_height == initial_scroll_height:
                break
            initial_scroll_height = new_scroll_height
    
    def smooth_scroll(self, driver: webdriver.Chrome, duration: int = 15):
        """Execute smooth scrolling script"""
        smooth_scroll_script = f"""
        let intervalId = setInterval(function() {{
            window.scrollBy(0, 200);
        }}, 100);

        // Set a timeout to prevent infinite scrolling
        setTimeout(function() {{
            clearInterval(intervalId);
        }}, {duration * 1000}); // Stop scrolling after {duration} seconds
        """
        driver.execute_script(smooth_scroll_script)
        time.sleep(duration + 2)  # Wait for scrolling to complete
    
    def parse_table(self, table_element) -> str:
        """Parse HTML table into formatted text"""
        table_content = ""
        header_row = table_element.find('tr')
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all('th')]
            if headers:
                table_content += '\n' + '\t'.join(headers)
        
        for tr in table_element.find_all('tr')[1:]:  # Skip the header row
            row = [td.text.strip() for td in tr.find_all('td')]
            if row:
                table_content += '\n' + '\t'.join(row)
        return table_content
    
    def parse_list_tags(self, list_tag) -> str:
        """Parse HTML lists (ul, ol) into formatted text"""
        list_content = ""
        for li in list_tag.find_all('li', recursive=False):
            li_content = li.get_text().strip()
            nested_lists = li.find_all(['ul', 'ol'], recursive=False)
            for nested_list in nested_lists:
                li_content += '\n' + self.parse_list_tags(nested_list)
            list_content += '\n' + li_content
        return list_content
    
    def process_iframe(self, iframe_src: str) -> str:
        """Process iframe content and extract table data"""
        table_data = ""
        try:
            driver = self.get_driver()
            driver.implicitly_wait(5)
            driver.get(iframe_src)
            time.sleep(2)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                for tr in tables[0].find_all('tr'):
                    # Extract each row's cells and join with '\t'
                    row = '\t'.join(td.get_text().strip() for td in tr.find_all('td'))
                    table_data += row + '\n'
            driver.quit()
        except Exception:
            pass
        return table_data
    
    def parse_elements(self, driver: webdriver.Chrome, element) -> str:
        """Parse HTML elements and extract content"""
        page_content = ""
        processed_tags = set()
        
        def process_tag(tag):
            nonlocal page_content
            if tag in processed_tags:
                return
            processed_tags.add(tag)
            
            # Replace <br> tags with newlines
            for br in tag.find_all("br"):
                br.replace_with("\n")
                
            if tag.name in ['p', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                tag_content = tag.get_text().strip()
                if tag_content:
                    page_content += '\n' + tag_content
                return  # Skip child tags of these tags
            elif tag.name == 'table':
                table_content = self.parse_table(tag)
                page_content += '\n' + table_content
                return
            elif tag.name in ['ul', 'ol']:
                list_content = self.parse_list_tags(tag)
                page_content += '\n' + list_content
                return
            elif tag.name == 'iframe':
                iframe_src = tag.get('src')
                if iframe_src:
                    iframe_content = self.process_iframe(iframe_src)
                    page_content += '\n' + iframe_content
                return
            else:
                if tag.children:
                    for child in tag.children:
                        if isinstance(child, Tag):
                            process_tag(child)
                else:
                    tag_content = tag.get_text().strip()
                    if tag_content:
                        page_content += '\n' + tag_content

        # Process Selenium WebElement
        children = element.find_elements(By.XPATH, "./*")
        for child in children:
            if child.tag_name.lower() == "iframe":
                iframe_src = child.get_attribute('src')
                if iframe_src:
                    iframe_content = self.process_iframe(iframe_src)
                    page_content += iframe_content
            else:
                child_html = child.get_attribute('outerHTML')
                child_soup = BeautifulSoup(child_html, 'html.parser')
                for tag in child_soup.children:
                    if tag.name:
                        process_tag(tag)
        return page_content.strip()


