"""
QianXin blog crawler - integrated link collection, content extraction and LLM analysis
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
from utils.time_utils import normalize_datetime, get_date_only


class QianxinCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for QianXin security blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "qianxin")
        ContentExtractor.__init__(self)
        self.config = SOURCES["qianxin"]
        self.name = "qianxin"  # Add name attribute for compatibility
        self._content_driver = None
    
    def get_content_driver(self):
        """Get or create a dedicated WebDriver for content extraction"""
        if self._content_driver is None:
            self._content_driver = super().get_content_driver()
            self._content_driver.implicitly_wait(5)
        return self._content_driver
    
    def close_content_driver(self):
        """Close the dedicated content driver"""
        if self._content_driver:
            try:
                self._content_driver.quit()
            except Exception:
                pass
            self._content_driver = None
    
    def collect_links(self) -> int:
        """Collect links from QianXin blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            if page_index == 1:
                page_url = self.config["base_url"]
            else:
                page_url = self.config["url_pattern"].format(page_index)
            
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                recent_post_items = soup.find_all("article", class_="recent-post-item")
                
                for item in recent_post_items:
                    try:
                        # Extract date
                        time_elem = item.find('time', class_='time')
                        if not time_elem:
                            continue
                        raw_date = time_elem.get('datetime')
                        # Normalize using unified time_utils function
                        formatted_date = get_date_only(raw_date)
                        
                        # Extract link
                        link_elem = item.find("a", class_="title")
                        if not link_elem:
                            continue
                        href_value = link_elem.get('href')
                        full_link = "https://tianwen.qianxin.com" + href_value
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, full_link):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing QianXin item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing QianXin page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
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
        """Extract content from QianXin blog article"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Wait for main content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "post-content"))
            )
            
            # Find the article content container
            article_content = driver.find_element(By.CLASS_NAME, "post-content")
            content = self.parse_elements(driver, article_content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting QianXin content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete QianXin crawling pipeline:
        1. Collect links from QianXin blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting QianXin crawler pipeline...")
            
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
            
            self.logger.info(f"✅ QianXin crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ QianXin crawler failed: {e}"
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