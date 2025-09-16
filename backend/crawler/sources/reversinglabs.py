"""
ReversingLabs blog crawler - uses requests for security blog
"""

from ..base import RequestsCrawler
from ..config import SOURCES


class ReversingLabsCrawler(RequestsCrawler):
    """Crawler for ReversingLabs security blog"""
    
    def __init__(self):
        super().__init__("reversinglabs")
        self.config = SOURCES["reversinglabs"]
    
    def collect_links(self) -> int:
        """Collect links from ReversingLabs blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                blog_listing_item = soup.find("div", class_="blog__listing-item")
                if not blog_listing_item:
                    continue
                    
                article_rows = blog_listing_item.find_all("article", class_="blog__item")
                
                for article in article_rows:
                    try:
                        # Extract date
                        time_elem = article.find("time")
                        if not time_elem:
                            continue
                        datetime_str = time_elem.get('datetime')
                        
                        # Extract link
                        link_elem = article.find("a")
                        if not link_elem:
                            continue
                        article_link = link_elem.get('href')
                        
                        if not self.save_link(datetime_str, article_link):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing ReversingLabs item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing ReversingLabs page {page_index}: {e}")
            
            self.delay()
        
        return links_found
