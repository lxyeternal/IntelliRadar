"""
Socket blog crawler - uses requests for static content
"""

from ..base import RequestsCrawler
from ..config import SOURCES


class SocketCrawler(RequestsCrawler):
    """Crawler for Socket security blog"""
    
    def __init__(self):
        super().__init__("socket")
        self.config = SOURCES["socket"]
    
    def collect_links(self) -> int:
        """Collect links from Socket blog"""
        links_found = 0
        
        soup = self.get_soup(self.config["url"])
        if not soup:
            return 0
        
        try:
            css_vql929 = soup.find("div", class_="css-1vql929")
            if not css_vql929:
                return 0
                
            chakra_linkbox = css_vql929.find_all("article", class_="chakra-linkbox")
            
            for linkbox in chakra_linkbox:
                try:
                    # Extract date
                    css_rqbta = linkbox.find("div", class_="css-rqbta8")
                    if not css_rqbta:
                        continue
                        
                    date_str = css_rqbta.find_all("span")[-1].text.strip().replace("-", "").strip().lower()
                    formatted_date = self.parse_date(date_str)
                    
                    # Extract link
                    chakra_heading = linkbox.find("h3", class_="chakra-heading")
                    if not chakra_heading:
                        continue
                        
                    href_div = chakra_heading.find("a", class_="chakra-linkbox__overlay")
                    if not href_div:
                        continue
                        
                    href_value = href_div.get('href')
                    full_link = "https://socket.dev" + href_value
                    
                    if not self.save_link(formatted_date, full_link):
                        # Found duplicate, stop collecting
                        return links_found
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Socket item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Socket page: {e}")
        
        return links_found
