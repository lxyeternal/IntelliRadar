"""
GitHub Security Advisory crawler - integrated link collection and structured data extraction
Extracts structured vulnerability data from GitHub Security Advisories
Saves data directly as JSON without LLM analysis
"""

import time
import json
import os
from pathlib import Path
from typing import Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from utils.time_utils import normalize_datetime, get_date_only


class GitHubCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for GitHub Security Advisories with structured data extraction"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "github")
        ContentExtractor.__init__(self)
        self.config = SOURCES["github"]
        self.name = "github"  # Add name attribute for compatibility
        self._content_driver = None
        self._list_driver = None
    
    def get_content_driver(self):
        """Get or create a dedicated WebDriver for content extraction"""
        if self._content_driver is None:
            self._content_driver = super().get_content_driver()
            self._content_driver.implicitly_wait(5)
        return self._content_driver
    
    def get_list_driver(self):
        """Get or create a dedicated WebDriver for browsing article lists"""
        if self._list_driver is None:
            self._list_driver = super().get_content_driver()
            self._list_driver.implicitly_wait(5)
        return self._list_driver
    
    def close_content_driver(self):
        """Close the dedicated content driver"""
        if self._content_driver:
            try:
                self._content_driver.quit()
            except Exception:
                pass
            self._content_driver = None
    
    def close_list_driver(self):
        """Close the dedicated list driver"""
        if self._list_driver:
            try:
                self._list_driver.quit()
            except Exception:
                pass
            self._list_driver = None

    def convert_date_format(self, date_str: str) -> str:
        """Convert Socket.dev date format using unified time_utils function"""
        try:
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self) -> int:
        """Collect links from GitHub Security Advisory pages using Selenium"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            
            try:
                # Use Selenium for GitHub pages
                driver = self.get_list_driver()
                driver.get(page_url)
                driver.implicitly_wait(10)
                
                # Find navigation container and items
                navigation_container = driver.find_element(By.CLASS_NAME, "js-active-navigation-container")
                navigation_items = navigation_container.find_elements(By.CLASS_NAME, "js-navigation-item")
                
                for navigation_item in navigation_items:
                    try:
                        # Extract date from relative-time element
                        datetime = navigation_item.find_element(By.TAG_NAME, "relative-time").get_attribute("datetime")
                        formatted_date = self.convert_date_format(datetime)
                        
                        # Extract link
                        href_value = navigation_item.find_element(By.TAG_NAME, "a").get_attribute("href")
                        print("github", formatted_date, href_value)
                        
                        # Use GitHub-specific processing method with structured data extraction
                        if not self.process_discovered_link_with_structured_data(formatted_date, href_value):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                        
                        # Print progress
                        print("github", formatted_date, href_value)
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing GitHub navigation item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing GitHub page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
    def process_discovered_link_with_structured_data(self, post_date: str, url: str) -> bool:
        """
        GitHub-specific link processing with structured data extraction
        Returns False if duplicate found (should stop), True to continue
        """
        # Check if already processed
        if self.storage.is_duplicate(url):
            self.logger.info(f"Duplicate found: {url}")
            return False
        
        # Extract structured data from GitHub advisory
        structured_data = self.extract_github_structured_data(url)
        if not structured_data:
            self.logger.warning(f"Failed to extract structured data from {url}")
            # Still save the link even if data extraction failed
            self.storage.save_link_entry(self.name, url, post_date)
            return True
        
        # Use Storage's unified method to ensure timestamp consistency
        timestamp = self.storage.save_github_link_with_verify_data(url, post_date, structured_data)
        
        self.logger.info(f"Successfully processed GitHub advisory: {url} (timestamp: {timestamp})")
        return True
    
    def extract_github_structured_data(self, url: str) -> Optional[Dict]:
        """Extract structured data from GitHub Security Advisory"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            # Find main article element
            article_main = driver.find_element(By.TAG_NAME, "main")
            
            # Extract title/summary
            subhead_description = article_main.find_element(By.CLASS_NAME, "Subhead-description")
            # title = subhead_description.find_element(By.CLASS_NAME, "v-align-middle").text.strip()
            
            # Extract datetime
            datetime = subhead_description.find_element(By.TAG_NAME, "relative-time").get_attribute("datetime")
            formatted_date = self.convert_date_format(datetime)
            # Extract package information
            table_content = article_main.find_element(By.CSS_SELECTOR, ".gutter-lg.gutter-condensed.clearfix")
            
            # Package name and manager
            name_manager = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-12.col-md-6.pr-md-2")
            package_name = name_manager.find_element(By.CSS_SELECTOR, ".f4.color-fg-default.text-bold").text.strip()
            manager_name = name_manager.find_element(By.CSS_SELECTOR, ".color-fg-muted.f4.d-inline-flex").text
            manager_name = manager_name.replace("(", "").replace(")", "").strip()
            # Version - extract all versions as a list
            version_div = table_content.find_element(By.CSS_SELECTOR, ".float-left.col-6.col-md-3.py-2.py-md-0.pr-2")
            version_elements = version_div.find_elements(By.CSS_SELECTOR, ".f4.color-fg-default")
            versions = [element.text.strip() for element in version_elements if element.text.strip()]
            # Description
            description_div = table_content.find_element(By.CSS_SELECTOR, ".Box-body.px-5.pb-5")
            description = description_div.text

            # Weakness/vulnerability details
            right_table = article_main.find_element(By.CSS_SELECTOR, ".col-12.col-md-3.float-left.pt-3.pt-md-0")
            # Extract GHSA ID from color-fg-muted elements
            ghsa_id = None
            color_muted_elements = right_table.find_elements(By.CSS_SELECTOR, ".color-fg-muted")
            for element in color_muted_elements:
                text = element.text.strip()
                if text.startswith("GHSA"):
                    ghsa_id = text
                    break
            print("github", ghsa_id)
            # weakness = right_table.find_element(By.CSS_SELECTOR, ".discussion-sidebar-item.js-repository-advisory-details").text.strip()
            
            # Structure the data
            structured_data = {
                "datetime": formatted_date,
                "package_name": package_name,
                "package_manager": manager_name,
                "versions": versions,
                "description": description,
                "ghsa_id": ghsa_id,
                "url": url
            }
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"Error extracting GitHub structured data from {url}: {e}")
            return None
    
    
    def run(self) -> dict:
        """
        Main method to execute the complete GitHub Security Advisory crawling pipeline:
        1. Collect links from GitHub Advisory pages
        2. Extract structured data from each advisory
        3. Save data as timestamped verify JSON files
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting GitHub Security Advisory crawler pipeline...")
            
            # Step 1: Collect links with integrated structured data extraction
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ GitHub crawler completed successfully: {links_found} advisories processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ GitHub crawler failed: {e}"
            self.logger.error(error_msg)
            return {
                'source': self.name,
                'links_found': 0,
                'status': 'failed',
                'error': str(e)
            }
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources after crawling"""
        self.close_content_driver()