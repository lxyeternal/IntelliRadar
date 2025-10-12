"""
Snyk crawler - integrated link collection, content extraction and LLM analysis
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


class SnykCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Snyk blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "snyk")
        ContentExtractor.__init__(self)
        self.config = SOURCES["snyk"]
        self.name = "snyk"  # Add name attribute for compatibility
        self._content_driver = None
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
    
    def close_content_driver(self):
        """Close the dedicated content driver"""
        if self._content_driver:
            try:
                self._content_driver.quit()
            except Exception:
                pass
            self._content_driver = None

    def convert_date_format(self, date_str: str) -> str:
        """Convert Snyk date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self):
        """Collect links from Snyk blog pages"""
        
        base_url = self.config["url_pattern"]
        max_pages = self.config["max_pages"]
        # Iterate through pages 1-10 based on original logic
        for page_index in range(1, max_pages + 1):
            # Use url_pattern from config
            page_url = base_url.format(page_index)
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                # Find article blocks using exact selectors from reference code
                news_blogs = soup.find_all("article", class_="card h-full")
                
                if not news_blogs:
                    self.logger.info(f"No more articles found on page {page_index}, stopping")
                    break
                
                # Process articles
                for news_blog in news_blogs:
                    try:
                        # Extract date info from paragraph
                        date_elem = news_blog.find("p", class_="txt-body txt-ui-body txt-line-clamp-4")
                        if date_elem:
                            datetime_str = date_elem.text.strip().lower()
                            formatted_date = self.convert_date_format(datetime_str)
                        else:
                            formatted_date = "None"
                        
                        # Extract article link
                        link_elem = news_blog.find("a", class_="button glyph marg-t-auto link-stretched")
                        if not link_elem:
                            continue
                            
                        news_href = link_elem.get('href')
                        if not news_href:
                            continue
                        
                        # Make URL absolute
                        full_link = "https://snyk.io" + news_href
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, full_link):
                            # Found duplicate, stop this page
                            return
                        
                        # Print progress
                        print("snyk", formatted_date, full_link)
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Snyk item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Snyk page {page_index}: {e}")
            
            self.delay()
    
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
        """Extract content from Snyk blog article using txt-rich-long class"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for main content to load using exact selector from reference code
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "txt-rich-long")))
            article_content = driver.find_element(By.CLASS_NAME, "txt-rich-long")
            
            if article_content:
                content = self.parse_elements(driver, article_content)
                return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting Snyk content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Snyk crawling pipeline:
        1. Collect links from Snyk blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        from datetime import datetime
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Starting Snyk crawler pipeline...")
            
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
            
            self.logger.info(f"✅ Snyk crawler completed: {self.stats['links_discovered']} discovered, "
                           f"{self.stats['content_saved']} content saved, {self.stats['links_failed']} failed")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"❌ Snyk crawler failed: {e}"
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
