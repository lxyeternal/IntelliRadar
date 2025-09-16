"""
Fortinet blog crawler - uses Selenium for threat research blog
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES


class FortinetCrawler(SeleniumCrawler):
    """Crawler for Fortinet Threat Research blog"""
    
    def __init__(self):
        super().__init__("fortinet")
        self.config = SOURCES["fortinet"]
    
    def collect_links(self) -> int:
        """Collect links from Fortinet blog with load more functionality"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        # Click load more buttons
        flag = self.config["max_load_more"]
        while flag:
            flag -= 1
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "b3-blog-list__pagination"))
                )
                more_button = self.driver.find_element(By.CLASS_NAME, "btn")
                more_button.click()
                self.driver.implicitly_wait(5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except:
                break
        
        time.sleep(2)
        
        try:
            infinite_hits_items = self.driver.find_elements(By.CSS_SELECTOR, ".b3-blog-list__post.text-container")
            
            for item in infinite_hits_items:
                try:
                    # Extract link
                    hit_title = item.find_element(By.CLASS_NAME, "b3-blog-list__background").find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Extract date
                    b3_blog_list__meta = item.find_element(By.CLASS_NAME, "b3-blog-list__meta")
                    datetime_str = b3_blog_list__meta.find_elements(By.TAG_NAME, "span")[1].text.strip().lower()
                    formatted_date = self.parse_date(datetime_str)
                    
                    if not self.save_link(formatted_date, hit_title):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Fortinet item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Fortinet page: {e}")
        
        return links_found
