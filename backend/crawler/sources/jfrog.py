"""
JFrog blog crawler - uses Selenium for pagination
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import NoSuchElementException

from ..base import SeleniumCrawler
from ..config import SOURCES


class JfrogCrawler(SeleniumCrawler):
    """Crawler for JFrog security blog"""
    
    def __init__(self):
        super().__init__("jfrog")
        self.config = SOURCES["jfrog"]
    
    def collect_links(self) -> int:
        """Collect links from JFrog blog with pagination"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        self.driver.implicitly_wait(10)
        
        # Initial scroll and load
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        count = 0
        while count < self.config["max_pages"]:
            try:
                # Process current page
                posts_wrap = self.driver.find_element(By.CLASS_NAME, "posts-wrap")
                blog_posts = posts_wrap.find_elements(By.CSS_SELECTOR, ".col-md-6.blog-post-title")
                
                for blog_post in blog_posts:
                    try:
                        # Extract date
                        post_date = blog_post.find_element(By.CLASS_NAME, "blog-post-date").text.split()[:3]
                        date_str = ' '.join(post_date).lower()
                        formatted_date = self.parse_date(date_str)
                        
                        # Extract link
                        blog_post_link = blog_post.find_element(By.TAG_NAME, "a").get_attribute("href")
                        
                        if not self.save_link(formatted_date, blog_post_link):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing JFrog item: {e}")
                
                # Try to go to next page
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".next a"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(10)
                
                # Wait for new page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "posts-wrap"))
                )
                count += 1
                
            except NoSuchElementException:
                self.logger.info("No 'Next' button found, possibly reached the last page")
                break
            except Exception as e:
                self.logger.error(f"An error occurred on JFrog page {count}: {str(e)}")
                break
        
        return links_found
