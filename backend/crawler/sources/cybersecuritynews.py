"""
Cybersecurity News crawler - uses requests for security news search
"""

from datetime import datetime
from ..base import RequestsCrawler
from ..config import SOURCES


class CybersecurityNewsCrawler(RequestsCrawler):
    """Crawler for Cybersecurity News"""
    
    def __init__(self):
        super().__init__("cybersecuritynews")
        self.config = SOURCES["cybersecuritynews"]
    
    def collect_links(self) -> int:
        """Collect links from Cybersecurity News search pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            for package_manage in self.config["search_terms"]:
                page_url = self.config["url_pattern"].format(page_index, package_manage)
                soup = self.get_soup(page_url)
                
                if not soup:
                    continue
                
                try:
                    latest_news_block = soup.find_all("div", class_="td_module_16 td_module_wrap td-animation-stack")
                    
                    for article in latest_news_block:
                        try:
                            # Extract date
                            post_date_elem = article.find("span", class_="td-post-date")
                            if not post_date_elem:
                                continue
                            time_elem = post_date_elem.find("time")
                            if not time_elem:
                                continue
                                
                            post_date = time_elem.get('datetime')
                            parsed_date = datetime.strptime(post_date, "%Y-%m-%dT%H:%M:%S%z")
                            formatted_date = parsed_date.strftime("%Y-%m-%d")
                            
                            # Extract link
                            link_elem = article.find("a")
                            if not link_elem:
                                continue
                            article_link = link_elem.get('href')
                            
                            if not self.save_link(str(formatted_date), article_link):
                                # Found duplicate, stop collecting
                                return links_found
                            links_found += 1
                        
                        except Exception as e:
                            self.logger.warning(f"Error parsing Cybersecurity News item: {e}")
                
                except Exception as e:
                    self.logger.error(f"Error processing Cybersecurity News page {page_index} for {package_manage}: {e}")
                
                self.delay()
        
        return links_found
