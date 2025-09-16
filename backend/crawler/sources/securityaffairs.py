"""
Security Affairs blog crawler - uses requests for security news
"""

from typing import Optional
from ..base import RequestsCrawler
from ..config import SOURCES
from ..content_extractor import SourceContentExtractor


class SecurityAffairsCrawler(RequestsCrawler):
    """Crawler for Security Affairs blog"""
    
    def __init__(self):
        super().__init__("securityaffairs")
        self.config = SOURCES["securityaffairs"]
        self.content_extractor = SourceContentExtractor()
    
    def collect_links(self) -> int:
        """Collect links from Security Affairs blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                latest_news_block = soup.find("div", class_="latest-news-block")
                if not latest_news_block:
                    continue
                    
                article_rows = latest_news_block.find_all("div", class_="news-card news-card-category mb-3 mb-lg-5")
                
                for article in article_rows:
                    try:
                        # Extract date
                        post_time = article.find("div", class_="post-time mb-3")
                        if not post_time:
                            continue
                        datetime_str = post_time.find_all("span")[1].text.strip().lower()
                        formatted_date = self.parse_date(datetime_str)
                        
                        # Extract link
                        link_elem = article.find("a")
                        if not link_elem:
                            continue
                        article_link = link_elem.get('href')
                        
                        if not self.process_discovered_link(formatted_date, article_link, self.extract_content):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Security Affairs item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Security Affairs page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from Security Affairs article using shared content extractor"""
        return self.content_extractor.extract_securityaffairs_content(url)
