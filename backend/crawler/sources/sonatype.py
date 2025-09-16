"""
Sonatype blog crawler - uses requests with date parsing
"""

import re
from ..base import RequestsCrawler
from ..config import SOURCES


class SonatypeCrawler(RequestsCrawler):
    """Crawler for Sonatype security blog"""
    
    def __init__(self):
        super().__init__("sonatype")
        self.config = SOURCES["sonatype"]
    
    def collect_links(self) -> int:
        """Collect links from Sonatype blog pages"""
        links_found = 0
        
        for page in range(self.config["max_pages"]):
            url = self.config["url_pattern"].format(page)
            soup = self.get_soup(url)
            
            if not soup:
                continue
            
            # Find blog section
            blog_section = soup.find(class_='resources mt-5')
            if not blog_section:
                continue
            
            # Find resource cards
            cards = blog_section.find_all(class_='resource-card col-12 col-md-12 col-lg-4 mb-3')
            
            for card in cards:
                try:
                    # Find listing boxes within card
                    listing_boxes = card.find_all("div", class_="span4 listing-box")
                    
                    for box in listing_boxes:
                        # Extract link
                        behind = box.find(class_="behind")
                        if not behind:
                            continue
                        
                        link_elem = behind.find('a', class_='hs-featured-image-link')
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href')
                        if not href:
                            continue
                        
                        # Extract and parse date
                        date_elem = box.find("div", class_="hubspot-editable")
                        if not date_elem:
                            continue
                        
                        date_text = date_elem.text.strip()
                        formatted_date = self._parse_sonatype_date(date_text)
                        
                        if not self.save_link(formatted_date, href):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Sonatype card: {e}")
            
            self.delay()
        
        return links_found
    
    def _parse_sonatype_date(self, date_text: str) -> str:
        """Parse Sonatype-specific date format"""
        pattern = r"\b(\w+)\s+(\d{1,2}),\s+(\d{4})\b"
        match = re.search(pattern, date_text)
        
        if match:
            month, day, year = match.groups()
            date_string = f"{month} {day}, {year}"
            return self.parse_date(date_string)
        
        return "None"
