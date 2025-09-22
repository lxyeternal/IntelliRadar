"""
Checkmarx Security Blog crawler - integrated link collection, content extraction and LLM analysis
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

class CheckmarxCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Checkmarx Security Blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "checkmarx")
        ContentExtractor.__init__(self)
        self.config = SOURCES["checkmarx"]
        self.name = "checkmarx"  # Add name attribute for compatibility
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
        """Collect links from Checkmarx Security Blog"""
        links_found = 0
        
        try:
            # Checkmarx blog uses pagination with "Load more" functionality
            driver = self.get_list_driver()  # Use separate driver for list browsing
            driver.get(self.config["url"])
            max_pages = self.config["max_load_more"]
            
            # Load more content by clicking "Load more" buttons (up to 5 times)
            for _ in range(max_pages):
                try:
                    load_more_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination-show-more a"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView();", load_more_link)
                    driver.execute_script("arguments[0].click();", load_more_link)
                    time.sleep(2)  # Give the page time to load new content
                except Exception as e:
                    self.logger.debug(f"'Load more' link not found or click failed: {str(e)}")
                    break  # Exit the loop if the link doesn't exist or the click fails
                    
            time.sleep(5)
            
            # Process all loaded blog posts
            premium_blog_posts = driver.find_elements(By.CSS_SELECTOR, ".card-post.card-post__second-version.card-post__v4")
            
            for premium_blog_post in premium_blog_posts:
                try:
                    # Extract link
                    news_href = premium_blog_post.find_element(By.TAG_NAME, "a").get_attribute("href").strip()
                    
                    # Extract date from card-post__title
                    datetime_str = premium_blog_post.find_element(By.CLASS_NAME, "card-post__title").text.strip().lower()
                    formatted_date = self.convert_date_format(datetime_str)
                    
                    if not formatted_date:
                        self.logger.warning(f"Could not parse date from: {datetime_str}")
                        continue
                    
                    # Use enhanced pipeline processing method with LLM analysis
                    if not self.process_discovered_link_with_analysis(formatted_date, news_href):
                        # Found duplicate, but continue processing other articles
                        continue
                    links_found += 1
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Checkmarx blog item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Checkmarx blog page: {e}")
        
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
        """Extract content from Checkmarx Security Blog article"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for and find the <article> element
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Find the main content in <article> tag
            article_content = driver.find_element(By.TAG_NAME, "article")
            content = self.parse_elements(driver, article_content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting Checkmarx content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Checkmarx crawling pipeline:
        1. Collect links from Checkmarx Security Blog
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Checkmarx Security Blog crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ Checkmarx crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Checkmarx crawler failed: {e}"
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
