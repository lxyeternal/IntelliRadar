"""
Datadog Security Labs crawler - uses Selenium for infinite scroll
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES


class DatadoghqCrawler(SeleniumCrawler):
    """Crawler for Datadog Security Labs"""
    
    def __init__(self):
        super().__init__("datadoghq")
        self.config = SOURCES["datadoghq"]
    
    def collect_links(self) -> int:
        """Collect links from Datadog Security Labs with infinite scroll"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        # Load more content by clicking "Load more" buttons
        while True:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ais-InfiniteHits-loadMore"))
                )
                more_button = self.driver.find_element(By.CLASS_NAME, "ais-InfiniteHits-loadMore")
                more_button.click()
                self.driver.implicitly_wait(5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except:
                break
        
        time.sleep(2)
        
        try:
            infinite_hits_items = self.driver.find_elements(By.CLASS_NAME, "ais-InfiniteHits-item")
            
            for item in infinite_hits_items:
                try:
                    # Extract date
                    datetime_str = item.find_elements(By.CLASS_NAME, "hit-header-text")[1].text.strip().lower()
                    formatted_date = self.parse_date(datetime_str)
                    
                    # Extract link
                    hit_title = item.find_element(By.CLASS_NAME, "hit-title-link").get_attribute("href")
                    
                    if not self.save_link(formatted_date, hit_title):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Datadog item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Datadog page: {e}")
        
        return links_found
