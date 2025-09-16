"""
Medium blog crawlers - multiple Medium sources
"""

import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES


class MediumCrawler(SeleniumCrawler):
    """Crawler for Medium security blog"""
    
    def __init__(self):
        super().__init__("medium")
        self.config = SOURCES["medium"]
    
    def collect_links(self) -> int:
        """Collect links from Medium security blog"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        # Scroll to load more content
        for _ in range(self.config["max_scroll"]):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        try:
            news_rows = self.driver.find_elements(By.CSS_SELECTOR, ".u-marginLeftNegative12.u-marginRightNegative12")
            
            for news_row in news_rows:
                news_divs = news_row.find_elements(By.CLASS_NAME, "u-marginBottom30")
                
                for news_div in news_divs:
                    try:
                        datetime_str = news_div.find_element(By.TAG_NAME, "time").get_attribute("datetime").strip()
                        news_href = news_div.find_element(By.TAG_NAME, "a").get_attribute("href")
                        news_href = news_href.split("?source")[0].strip()
                        
                        if not self.save_link(datetime_str, news_href):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Medium item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error loading Medium page: {e}")
        
        return links_found


class MediumRecommandCrawler(SeleniumCrawler):
    """Crawler for Medium recommended supply chain security articles"""
    
    def __init__(self):
        super().__init__("medium_recommand")
        self.config = SOURCES["medium_recommand"]
    
    def collect_links(self) -> int:
        """Collect links from Medium recommended articles"""
        links_found = 0
        
        if not self.get_page(self.config["url"]):
            return 0
        
        self.driver.implicitly_wait(10)
        
        # Extensive scrolling for recommended articles
        for count in range(self.config["max_scroll"]):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        try:
            news_blogs = self.driver.find_elements(By.CSS_SELECTOR, ".bg.jd.je.jf.jg")
            
            for news_blog in news_blogs:
                try:
                    news_url_div = news_blog.find_element(By.CSS_SELECTOR, ".l.er.ju")
                    news_url = news_url_div.find_element(By.TAG_NAME, "a").get_attribute("href").strip().split("?source")[0].strip()
                    
                    datetime_str = news_blog.find_element(By.CSS_SELECTOR, ".lg.db.lh.dd.li.df.lk.ll .ab").text.strip()
                    datetime_str_split = datetime_str.split("\n")[0].strip().lower()
                    
                    # Parse different date formats
                    formatted_date = self._parse_medium_date(datetime_str_split)
                    
                    if not self.save_link(formatted_date, news_url):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Medium recommended item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error loading Medium recommended page: {e}")
        
        return links_found
    
    def _parse_medium_date(self, datetime_str_split: str) -> str:
        """Parse Medium-specific date formats"""
        try:
            # Handle "X days ago" format
            if "days ago" in datetime_str_split or "d ago" in datetime_str_split:
                days_ago = int(datetime_str_split.split()[0])
                specific_date = datetime.now() - timedelta(days=days_ago)
                return specific_date.strftime('%Y-%m-%d')
            else:
                try:
                    # Handle "Feb 1" format (current year)
                    specific_date = datetime.strptime(datetime_str_split, '%b %d')
                    specific_date = specific_date.replace(year=datetime.now().year)
                    return specific_date.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        # Handle "Sep 24, 2023" format
                        specific_date = datetime.strptime(datetime_str_split, '%b %d, %Y')
                        return specific_date.strftime('%Y-%m-%d')
                    except ValueError:
                        # Fallback to standard parser
                        return self.parse_date(datetime_str_split)
        except Exception:
            return "None"
