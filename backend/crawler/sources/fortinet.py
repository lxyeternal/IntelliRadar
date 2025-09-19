"""
Fortinet Threat Research crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
import json
import os
from pathlib import Path
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import get_date_only

class FortinetCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Fortinet Threat Research with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "fortinet")
        ContentExtractor.__init__(self)
        self.config = SOURCES["fortinet"]
        self.name = "fortinet"  # Add name attribute for compatibility
        self._content_driver = None
        self._list_driver = None  # Separate driver for browsing article lists
    
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
    
    def collect_links(self) -> int:
        """Collect links from Fortinet Threat Research blog"""
        links_found = 0
        
        try:
            driver = self.get_list_driver()
            driver.get(self.config["url"])
            
            # Load more content by clicking "Load More" buttons - up to max_load_more times
            max_clicks = self.config.get("max_load_more", 20)
            flag = max_clicks
            
            while flag:
                flag -= 1
                try:
                    # Wait for pagination to be present and clickable
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "b3-blog-list__pagination"))
                    )
                    more_button = driver.find_element(By.CLASS_NAME, "btn")
                    
                    # Check if button is still clickable/visible
                    if not more_button.is_enabled() or not more_button.is_displayed():
                        self.logger.info("Load more button is no longer available")
                        break
                    
                    more_button.click()
                    driver.implicitly_wait(5)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.info(f"No more content to load or error clicking load more: {e}")
                    break
            
            time.sleep(2)
            
            # Process all loaded articles
            infinite_hits_items = driver.find_elements(By.CSS_SELECTOR, ".b3-blog-list__post.text-container")
            
            if not infinite_hits_items:
                self.logger.warning("No articles found on Fortinet blog")
                return 0
            
            self.logger.info(f"Found {len(infinite_hits_items)} articles on Fortinet blog")
            
            for item in infinite_hits_items:
                try:
                    # Extract link from the background element
                    hit_title_element = item.find_element(By.CLASS_NAME, "b3-blog-list__background")
                    link_element = hit_title_element.find_element(By.TAG_NAME, "a")
                    article_url = link_element.get_attribute("href")
                    
                    # Extract date from meta information
                    b3_blog_list_meta = item.find_element(By.CLASS_NAME, "b3-blog-list__meta")
                    date_spans = b3_blog_list_meta.find_elements(By.TAG_NAME, "span")
                    
                    if len(date_spans) < 2:
                        self.logger.warning(f"Could not find date for article: {article_url}")
                        continue
                    
                    datetime_str = date_spans[1].text.strip().lower()
                    formatted_date = self.convert_date_format(datetime_str)
                    
                    if not formatted_date:
                        self.logger.warning(f"Could not parse date '{datetime_str}' for article: {article_url}")
                        continue
                    
                    # Use enhanced pipeline processing method with LLM analysis
                    if not self.process_discovered_link_with_analysis(formatted_date, article_url):
                        # Found duplicate, but continue processing other articles
                        continue
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Fortinet article item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Fortinet blog page: {e}")
        
        return links_found
    
    def convert_date_format(self, date_string):
        """Convert date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_string)
            return formatted_date
        except Exception:
            return None
    
    def process_discovered_link_with_analysis(self, post_date: str, url: str) -> bool:
        """
        Enhanced link processing with LLM analysis using unified StorageManager
        Returns False if duplicate found (should stop), True to continue
        """
        # Check if already processed
        if self.storage.is_duplicate(url):
            self.logger.info(f"Duplicate found: {url}")
            return False
        
        # Extract content
        print(f"Extracting content from {url}...")
        content = self.extract_content(url)
        if not content:
            self.logger.warning(f"Failed to extract content from {url}")
            # Still save the link even if content extraction failed
            self.storage.save_link_entry(self.name, url, post_date)
            return True
        
        # Perform LLM analysis
        self.logger.info(f"Performing LLM analysis for {url}...")
        analyzer = IntelligenceAnalyzer()
        analysis_result = analyzer.analyze_content(content)
        
        # Save link with content and analysis results using unified storage
        timestamp = self.storage.save_link_with_analysis(
            self.name, url, post_date, content, analysis_result
        )
        
        self.logger.info(f"Successfully processed and analyzed: {url} (timestamp: {timestamp})")
        return True
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from Fortinet Threat Research article"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for main content to load - Fortinet uses AEM Grid system
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".aem-Grid.aem-Grid--12.aem-Grid--default--12"))
            )
            
            # Find the article content container
            article_content = driver.find_element(By.CSS_SELECTOR, ".aem-Grid.aem-Grid--12.aem-Grid--default--12")
            content = self.parse_elements(driver, article_content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting Fortinet content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Fortinet crawling pipeline:
        1. Collect links from Fortinet Threat Research blog
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Fortinet Threat Research crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_locations': {
                    'links': str(self.storage.links_file),
                    'content': str(self.storage.content_dir / self.name),
                    'analysis': str(self.storage.json_dir / self.name)
                }
            }
            
            self.logger.info(f"✅ Fortinet crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Fortinet crawler failed: {e}"
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
        self.close_list_driver()
