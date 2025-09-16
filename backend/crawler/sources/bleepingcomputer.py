"""
BleepingComputer blog crawler - uses Selenium for dynamic content
"""

import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES
from ..content_extractor import SourceContentExtractor


class BleepingComputerCrawler(SeleniumCrawler):
    """Crawler for BleepingComputer blog"""
    
    def __init__(self):
        super().__init__("bleepingcomputer")
        self.config = SOURCES["bleepingcomputer"]
        self.content_extractor = SourceContentExtractor()
    
    def collect_links(self) -> int:
        """Collect links from BleepingComputer blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            if page_index == 1:
                pageurl = self.config["base_url"]
            else:
                pageurl = self.config["url_pattern"].format(page_index)
            
            if not self.get_page(pageurl):
                continue
            
            try:
                # Wait for news container
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "bc-home-news-main-wrap"))
                )
                self.driver.execute_script("window.stop();")  # Stop loading immediately
                
                bc_latest_news = self.driver.find_element(By.ID, "bc-home-news-main-wrap")
                bc_latest_news_imgs = bc_latest_news.find_elements(By.CLASS_NAME, "bc_latest_news_text")
                
                for li_tag in bc_latest_news_imgs:
                    try:
                        # Extract URL and date
                        li_url = li_tag.find_elements(By.TAG_NAME, "a")[1].get_attribute("href").strip()
                        datetime_str = li_tag.find_element(By.CLASS_NAME, "bc_news_date").text.strip()
                        formatted_date = self.parse_date(datetime_str.lower())
                        
                        if not self.process_discovered_link(formatted_date, li_url, self.extract_content):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing BleepingComputer item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error loading BleepingComputer page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from BleepingComputer article using shared content extractor"""
        return self.content_extractor.extract_bleepingcomputer_content(url)
