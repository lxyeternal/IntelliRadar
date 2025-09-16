"""
TuxCare blog crawler - uses Selenium for blog posts
"""

import time
from datetime import datetime
from selenium.webdriver.common.by import By

from ..base import SeleniumCrawler
from ..config import SOURCES


class TuxcareCrawler(SeleniumCrawler):
    """Crawler for TuxCare security blog"""
    
    def __init__(self):
        super().__init__("tuxcare")
        self.config = SOURCES["tuxcare"]
    
    def collect_links(self) -> int:
        """Collect links from TuxCare blog"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        time.sleep(2)
        
        try:
            infinite_hits_item = self.driver.find_element(By.CLASS_NAME, "blog-posts")
            posts = infinite_hits_item.find_elements(By.CLASS_NAME, "post")
            
            for item in posts:
                try:
                    # Extract link
                    hit_title = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Extract and parse date
                    post_date_element = item.find_element(By.CLASS_NAME, "post-date").find_element(By.TAG_NAME, "span")
                    datetime_str = post_date_element.get_attribute('outerHTML').replace('<span>', '').replace('</span>', '')
                    
                    date_obj = datetime.strptime(datetime_str, "%B %d, %Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    
                    if not self.save_link(formatted_date, hit_title):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing TuxCare item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing TuxCare page: {e}")
        
        return links_found
