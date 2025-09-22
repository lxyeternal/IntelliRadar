"""
RHISAC blog crawler - integrated link collection, content extraction and LLM analysis
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


class RHISACCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for RHISAC blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "rhisac")
        ContentExtractor.__init__(self)
        self.config = SOURCES["rhisac"]
        self.name = "rhisac"  # Add name attribute for compatibility
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

    def convert_date_format(self, date_str: str) -> str:
        """Convert CheckPoint date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self) -> int:
        """Collect links from RHISAC blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            # Use url_pattern directly with page_index, following original logic
            page_url = self.config["url_pattern"].format(page_index)
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                # Find all article blocks - exactly like original rhisac_blog logic
                articles = soup.find_all("article", class_="post inner-row")
                
                if not articles:
                    self.logger.info(f"No more articles found on page {page_index}, stopping")
                    break
                
                for article in articles:
                    try:
                        # Extract article link - exactly like original logic
                        link_element = article.find("a")
                        if not link_element:
                            continue
                            
                        article_url = link_element.get('href', '').strip()
                        if not article_url:
                            continue
                            
                        # Make URL absolute if needed
                        if not article_url.startswith('http'):
                            article_url = "https://rhisac.org" + article_url
                        
                        # Extract date - exactly like original logic
                        date_element = article.find("p", class_="mb-0")
                        if date_element:
                            date_text = date_element.get_text(strip=True)
                            # Remove "Posted on " prefix and clean up - exactly like original
                            date_text = date_text.replace("Posted on ", "").strip().lower()
                            # Use unified time_utils function
                            formatted_date = self.convert_date_format(date_text)
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, article_url):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing RHISAC item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing RHISAC page {page_index}: {e}")
            
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
        """Extract content from RHISAC blog article - following original rhisac_content logic"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)  # Exactly like original
            driver.get(url)
            
            # Scroll to load all content - exactly like original
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for main content to load - exactly like original
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".elementor-widget.elementor-widget-theme-post-content"))
            )
            
            # Find the article content container - exactly like original
            elementor_widget = driver.find_element(By.CSS_SELECTOR, ".elementor-widget.elementor-widget-theme-post-content")
            article_content = elementor_widget.find_element(By.CLASS_NAME, "elementor-widget-container")
            content = self.parse_elements(driver, article_content)
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting RHISAC content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete RHISAC crawling pipeline:
        1. Collect links from RHISAC blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting RHISAC crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ RHISAC crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ RHISAC crawler failed: {e}"
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