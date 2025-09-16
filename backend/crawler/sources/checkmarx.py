"""
Checkmarx blog crawler - uses Selenium for dynamic content loading
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES


class CheckmarxCrawler(SeleniumCrawler):
    """Crawler for Checkmarx security blog"""
    
    def __init__(self):
        super().__init__("checkmarx")
        self.config = SOURCES["checkmarx"]
    
    def collect_links(self) -> int:
        """Collect links from Checkmarx blog with load more functionality"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        # Click "Load more" buttons
        for _ in range(self.config["max_load_more"]):
            try:
                load_more_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination-show-more a"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more_link)
                self.driver.execute_script("arguments[0].click();", load_more_link)
                time.sleep(2)  # Give page time to load new content
            except Exception as e:
                self.logger.info(f"'Load more' link not found or click failed: {str(e)}")
                break  # Exit if no more "Load more" buttons
        
        time.sleep(5)  # Final wait for all content to load
        
        try:
            premium_blog_posts = self.driver.find_elements(By.CSS_SELECTOR, ".card-post.card-post__second-version.card-post__v4")
            
            for premium_blog_post in premium_blog_posts:
                try:
                    # Extract link
                    news_href = premium_blog_post.find_element(By.TAG_NAME, "a").get_attribute("href").strip()
                    
                    # Extract date
                    datetime_str = premium_blog_post.find_element(By.CLASS_NAME, "card-post__title").text.strip().lower()
                    formatted_date = self.parse_date(datetime_str)
                    
                    if not self.save_link(formatted_date, news_href):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Checkmarx item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Checkmarx page: {e}")
        
        return links_found
