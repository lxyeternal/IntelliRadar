"""
Check Point research crawler - uses requests for threat intelligence
"""

from ..base import RequestsCrawler
from ..config import SOURCES


class CheckpointCrawler(RequestsCrawler):
    """Crawler for Check Point Research"""
    
    def __init__(self):
        super().__init__("checkpoint")
        self.config = SOURCES["checkpoint"]
    
    def collect_links(self) -> int:
        """Collect links from Check Point research pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                latest_news_block = soup.find_all("div", class_="box col-margin relative border-dotted")
                
                for article in latest_news_block:
                    try:
                        # Extract date
                        date_elem = article.find("div", class_="date small-font")
                        if not date_elem:
                            continue
                        post_date = date_elem.text.strip()
                        formatted_date = self.parse_date(post_date)
                        
                        # Extract link
                        link_elem = article.find("a")
                        if not link_elem:
                            continue
                        article_link = link_elem.get('href')
                        
                        if not self.save_link(formatted_date, article_link):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Check Point item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Check Point page {page_index}: {e}")
            
            self.delay()
        
        return links_found
