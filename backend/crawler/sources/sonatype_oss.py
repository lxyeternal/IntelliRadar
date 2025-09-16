"""
Sonatype OSS blog crawler - uses requests for open source security
"""

import re
from ..base import RequestsCrawler
from ..config import SOURCES


class SonatypeOssCrawler(RequestsCrawler):
    """Crawler for Sonatype OSS blog"""
    
    def __init__(self):
        super().__init__("sonatype_oss")
        self.config = SOURCES["sonatype_oss"]
    
    def collect_links(self) -> int:
        """Collect links from Sonatype OSS blog pages"""
        links_found = 0
        
        for page_index in range(self.config["max_pages"]):
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            
            if not soup:
                continue
            
            try:
                blog_sections = soup.find_all(class_='blog-section')
                if len(blog_sections) < 2:
                    continue
                    
                blog_section = blog_sections[1]
                row_fluids = blog_section.find_all(class_='row-fluid')
                
                for row_fluid in row_fluids:
                    listing_boxs = row_fluid.find_all("div", class_="span4 listing-box")
                    
                    for listing_box in listing_boxs:
                        try:
                            # Extract link
                            boxs_behind = listing_box.find(class_="behind")
                            if not boxs_behind:
                                continue
                                
                            a_tag = boxs_behind.find('a', class_='hs-featured-image-link')
                            if not a_tag:
                                continue
                                
                            href_value = a_tag.get('href').strip()
                            
                            # Extract and parse date
                            date_elem = listing_box.find("div", class_="hubspot-editable")
                            if not date_elem:
                                continue
                                
                            datetime_str = date_elem.text.strip()
                            formatted_date = self._parse_sonatype_date(datetime_str)
                            
                            if not self.save_link(formatted_date, href_value):
                                # Found duplicate, stop collecting
                                return links_found
                            links_found += 1
                        
                        except Exception as e:
                            self.logger.warning(f"Error parsing Sonatype OSS item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Sonatype OSS page {page_index}: {e}")
            
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
