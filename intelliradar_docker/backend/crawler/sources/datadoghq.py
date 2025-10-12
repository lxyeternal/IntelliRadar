"""
Datadog Security Labs crawler - integrated link collection, content extraction and LLM analysis
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

class DatadoghqCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Datadog Security Labs with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "datadoghq")
        ContentExtractor.__init__(self)
        self.config = SOURCES["datadoghq"]
        self.name = "datadoghq"  # Add name attribute for compatibility
        self._content_driver = None
        self._list_driver = None  # Separate driver for browsing article lists
        # Statistics tracking
        self.stats = {
            'links_discovered': 0,
            'content_saved': 0,
            'links_processed': 0,
            'links_failed': 0
        }
    
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
    
    def collect_links(self):
        """Collect links from Datadog Security Labs articles page"""
        
        try:
            # Datadog uses a single page with infinite scroll loading
            driver = self.get_list_driver()  # Use separate driver for list browsing
            driver.get(self.config["url"])
            
            # Load more content by clicking "Load More" buttons
            while True:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ais-InfiniteHits-loadMore"))
                    )
                    more_button = driver.find_element(By.CLASS_NAME, "ais-InfiniteHits-loadMore")
                    more_button.click()
                    driver.implicitly_wait(5)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                except:
                    break
            
            time.sleep(2)
            
            # Process all loaded articles
            infinite_hits_items = driver.find_elements(By.CLASS_NAME, "ais-InfiniteHits-item")
            
            for item in infinite_hits_items:
                try:
                    # Extract date - get the second element with class "hit-header-text"
                    hit_header_texts = item.find_elements(By.CLASS_NAME, "hit-header-text")
                    if len(hit_header_texts) < 2:
                        continue
                    
                    datetime_str = hit_header_texts[1].text.strip().lower()
                    formatted_date = self.convert_date_format(datetime_str)
                    
                    # Extract link
                    hit_title_link = item.find_element(By.CLASS_NAME, "hit-title-link")
                    article_url = hit_title_link.get_attribute("href")
                    
                    # Use enhanced pipeline processing method with LLM analysis
                    if not self.process_discovered_link_with_analysis(formatted_date, article_url):
                        # Found duplicate, but continue processing other articles
                        return
                
                except Exception as e:
                    self.logger.warning(f"Error parsing Datadog item: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing Datadog articles page: {e}")
    
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
        
        # Update statistics
        self.stats['links_discovered'] += 1
        self.stats['links_processed'] += 1
        
        # Extract content
        print(f"Extracting content from {url}...")
        content = self.extract_content(url)
        if not content:
            self.logger.warning(f"Failed to extract content from {url}")
            # Still save the link even if content extraction failed
            self.storage.save_link_entry(self.name, url, post_date)
            self.stats['links_failed'] += 1
            return True
        
        self.stats['content_saved'] += 1
        
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
        """Extract content from Datadog Security Labs article"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for main content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".article-content.relative"))
            )
            
            # Find the article content container
            article_content = driver.find_element(By.CSS_SELECTOR, ".article-content.relative")
            content = self.parse_elements(driver, article_content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting Datadog content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Datadog crawling pipeline:
        1. Collect links from Datadog Security Labs articles page
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        from datetime import datetime
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Starting Datadog Security Labs crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            self.collect_links()
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Generate summary with correct field names for TaskLogger
            result = {
                'source': self.name,
                'status': 'success',
                'links_discovered': self.stats['links_discovered'],
                'links_processed': self.stats['links_processed'],
                'content_saved': self.stats['content_saved'],
                'links_failed': self.stats['links_failed'],
                'duration': duration,
                'pipeline_mode': True
            }
            
            self.logger.info(f"✅ Datadog crawler completed: {self.stats['links_discovered']} discovered, "
                           f"{self.stats['content_saved']} content saved, {self.stats['links_failed']} failed")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"❌ Datadog crawler failed: {e}"
            self.logger.error(error_msg)
            return {
                'source': self.name,
                'status': 'failed',
                'links_discovered': self.stats['links_discovered'],
                'links_processed': self.stats['links_processed'],
                'content_saved': self.stats['content_saved'],
                'links_failed': self.stats['links_failed'],
                'duration': duration,
                'error': str(e)
            }
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources after crawling"""
        self.close_content_driver()
        self.close_list_driver()
