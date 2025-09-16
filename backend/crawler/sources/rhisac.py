"""
RH-ISAC blog crawler - uses requests for healthcare security blog
"""

from ..base import RequestsCrawler
from ..config import SOURCES


class RhisacCrawler(RequestsCrawler):
    """Crawler for RH-ISAC blog"""
    
    def __init__(self):
        super().__init__("rhisac")
        self.config = SOURCES["rhisac"]
    
    def collect_links(self) -> int:
        """Collect links from RH-ISAC blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                latest_news_block = soup.find_all("article", class_="post inner-row")
                
                for article in latest_news_block:
                    try:
                        # Extract link
                        link_elem = article.find("a")
                        if not link_elem:
                            continue
                        article_link = link_elem.get('href').strip()
                        
                        # Extract date
                        date_elem = article.find("p", class_="mb-0")
                        if not date_elem:
                            continue
                        datetime_text = date_elem.text.strip().replace("Posted on ", "").strip().lower()
                        formatted_date = self.parse_date(datetime_text)
                        
                        if not self.save_link(formatted_date, article_link):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing RH-ISAC item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing RH-ISAC page {page_index}: {e}")
            
            self.delay()
        
        return links_found
