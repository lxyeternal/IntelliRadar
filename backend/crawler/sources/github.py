"""
GitHub Advisory crawler - uses Selenium for JavaScript content
Now supports pipeline mode: discover links + extract content immediately
"""

import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..base import SeleniumCrawler
from ..config import SOURCES


class GitHubCrawler(SeleniumCrawler):
    """Crawler for GitHub Security Advisories"""
    
    def __init__(self):
        super().__init__("github")
        self.config = SOURCES["github"]
    
    def collect_links(self) -> int:
        """Collect links from GitHub advisory pages"""
        links_found = 0
        
        for page in range(1, self.config["max_pages"] + 1):
            url = self.config["url_pattern"].format(page)
            
            if not self.get_page(url):
                continue
            
            time.sleep(2)  # Wait for page to load
            
            try:
                # Wait for navigation container
                wait = WebDriverWait(self.driver, 10)
                nav_container = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "js-active-navigation-container"))
                )
                
                # Find all advisory items
                items = nav_container.find_elements(By.CLASS_NAME, "js-navigation-item")
                
                for item in items:
                    try:
                        # Extract datetime
                        time_elem = item.find_element(By.TAG_NAME, "relative-time")
                        datetime_str = time_elem.get_attribute("datetime")
                        
                        # Extract link
                        link_elem = item.find_element(By.TAG_NAME, "a")
                        href = link_elem.get_attribute("href")
                        
                        if datetime_str and href:
                            # Use new pipeline processing method
                            if not self.process_discovered_link(datetime_str, href, self.extract_content):
                                # Found duplicate, stop this page
                                return links_found
                            links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing GitHub item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error loading GitHub page {page}: {e}")
            
            self.delay()
        
        return links_found
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from GitHub Advisory page"""
        try:
            # Navigate to the advisory page
            if not self.get_page(url):
                return None
            
            time.sleep(2)  # Wait for page to load
            
            # Extract advisory information
            content_parts = []
            
            # Get main advisory content
            try:
                main_elem = self.driver.find_element(By.TAG_NAME, "main")
                
                # Title and description
                title_elem = main_elem.find_element(By.CSS_SELECTOR, ".f4.color-fg-default.text-bold")
                if title_elem:
                    content_parts.append(f"Title: {title_elem.text.strip()}")
                
                # Package info
                try:
                    package_elem = main_elem.find_element(By.CSS_SELECTOR, ".color-fg-muted.f4.d-inline-flex")
                    if package_elem:
                        content_parts.append(f"Package: {package_elem.text.strip()}")
                except:
                    pass
                
                # Description
                try:
                    desc_elem = main_elem.find_element(By.CSS_SELECTOR, ".Box-body.px-5.pb-5")
                    if desc_elem:
                        content_parts.append(f"Description: {desc_elem.text.strip()}")
                except:
                    pass
                
                # Weakness info
                try:
                    weakness_elem = main_elem.find_element(By.CSS_SELECTOR, ".discussion-sidebar-item.js-repository-advisory-details")
                    if weakness_elem:
                        content_parts.append(f"Weakness: {weakness_elem.text.strip()}")
                except:
                    pass
            
            except Exception as e:
                self.logger.warning(f"Error extracting main content from {url}: {e}")
                return None
            
            if not content_parts:
                self.logger.warning(f"No content extracted from GitHub advisory: {url}")
                return None
            
            return '\n\n'.join(content_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {e}")
            return None
