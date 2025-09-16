"""
Snyk blog crawler - uses requests for simple pagination
Now supports pipeline mode: discover links + extract content immediately
"""

from typing import Optional
from ..base import RequestsCrawler
from ..config import SOURCES
from ..content_extractor import SourceContentExtractor


class SnykCrawler(RequestsCrawler):
    """Crawler for Snyk security blog"""
    
    def __init__(self):
        super().__init__("snyk")
        self.config = SOURCES["snyk"]
        self.content_extractor = SourceContentExtractor()
    
    def collect_links(self) -> int:
        """Collect links from Snyk blog pages"""
        links_found = 0
        
        for page in range(1, self.config["max_pages"] + 1):
            url = self.config["url_pattern"].format(page)
            soup = self.get_soup(url)
            
            if not soup:
                continue
            
            # Find blog post containers
            posts = soup.find_all("div", class_="w-full marg-h-auto p-relative h-full")
            
            for post in posts:
                try:
                    # Extract date
                    date_elem = post.find("p", class_="txt-body txt-color-body txt-line-clamp-4")
                    if not date_elem:
                        continue
                    
                    date_str = self.parse_date(date_elem.text.strip())
                    
                    # Extract link
                    link_elem = post.find("a", class_="group txt-decoration-none")
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href')
                    if href:
                        full_url = f"https://snyk.io{href}"
                        # Use new pipeline processing method
                        if not self.process_discovered_link(date_str, full_url, self.extract_content):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Snyk post: {e}")
            
            self.delay()
        
        return links_found
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from Snyk blog article using shared content extractor"""
        return self.content_extractor.extract_snyk_content(url)
