"""
Phylum blog crawler - uses requests for security research blog
"""

from ..base import RequestsCrawler
from ..config import SOURCES


class PhylumCrawler(RequestsCrawler):
    """Crawler for Phylum security blog"""
    
    def __init__(self):
        super().__init__("phylum")
        self.config = SOURCES["phylum"]
    
    def collect_links(self) -> int:
        """Collect links from Phylum blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                # Find articles with different classes
                latest_news_block = soup.find_all("article", class_=[
                    "post tag-research", 
                    "post tag-insights", 
                    "post tag-research featured"
                ])
                
                # Skip first article on page 1 (usually featured)
                articles_to_process = latest_news_block[1:] if page_index == 1 else latest_news_block
                
                for article in articles_to_process:
                    try:
                        # Extract link
                        link_elem = article.find("a", class_="post-title-link")
                        if not link_elem:
                            continue
                        article_link = link_elem.get('href')
                        
                        # Extract date
                        time_elem = article.find("time")
                        if not time_elem:
                            continue
                        formatted_date = time_elem.get('datetime')
                        
                        full_link = "https://blog.phylum.io" + article_link
                        
                        if not self.save_link(formatted_date, full_link):
                            # Found duplicate, stop collecting
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Phylum item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Phylum page {page_index}: {e}")
            
            self.delay()
        
        return links_found
