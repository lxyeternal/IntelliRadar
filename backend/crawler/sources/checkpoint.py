"""
CheckPoint Research blog crawler - integrated link collection, content extraction and LLM analysis
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


class CheckpointCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for CheckPoint Research blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "checkpoint")
        ContentExtractor.__init__(self)
        self.config = SOURCES["checkpoint"]
        self.name = "checkpoint"  # Add name attribute for compatibility
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
        """Collect links from CheckPoint Research blog pages using requests (static scraping)"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            page_url = self.config["url_pattern"].format(page_index)
            
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                # Use the exact selectors from original working implementation
                latest_news_block = soup.find_all("div", class_="box col-margin relative border-dotted")
                
                for article in latest_news_block:
                    try:
                        # Extract date using original selector
                        date_elem = article.find("div", class_="date small-font")
                        if not date_elem:
                            continue
                        
                        post_date = date_elem.text.strip()
                        formatted_date = self.convert_date_format(post_date)
                        
                        # Extract link using original selector
                        link_elem = article.find("a")
                        if not link_elem:
                            continue
                        
                        article_link = link_elem.get('href')
                        if not article_link:
                            continue
                        
                        # Handle relative URLs
                        if article_link.startswith('/'):
                            full_link = "https://research.checkpoint.com" + article_link
                        elif article_link.startswith('http'):
                            full_link = article_link
                        else:
                            continue
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, full_link):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing CheckPoint item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing CheckPoint page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
    def convert_date_format(self, date_str: str) -> str:
        """Convert CheckPoint date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def process_discovered_link_with_analysis(self, post_date: str, url: str) -> bool:
        """
        Enhanced link processing with LLM analysis using unified StorageManager - reusing QianXin/DataDog implementation
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
        """Extract content from CheckPoint Research article using Selenium (dynamic scraping)"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to bottom to ensure content is loaded (from original implementation)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for content using original selector
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".text.border-bottom"))
            )
            
            # Extract content using original selector
            article_content = driver.find_element(By.CSS_SELECTOR, ".text.border-bottom")
            
            if article_content:
                content = self.parse_elements(driver, article_content)
                return content
            else:
                self.logger.warning(f"Could not find content container for {url}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error extracting CheckPoint content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete CheckPoint crawling pipeline - reusing QianXin/DataDog structure:
        1. Collect links from CheckPoint Research blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting CheckPoint crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ CheckPoint crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ CheckPoint crawler failed: {e}"
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
        """Clean up resources after crawling - reusing QianXin implementation"""
        self.close_content_driver()
