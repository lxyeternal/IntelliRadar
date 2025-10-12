"""
CyberSecurityNews crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import normalize_datetime, get_date_only


class CybersecuritynewsCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for CyberSecurityNews blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "cybersecuritynews")
        ContentExtractor.__init__(self)
        self.config = SOURCES["cybersecuritynews"]
        self.name = "cybersecuritynews"  # Add name attribute for compatibility
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
        """Convert CyberSecurityNews date format using unified time_utils function"""
        try:
            # CyberSecurityNews uses ISO format: "2024-01-15T10:30:00+00:00"
            parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            return parsed_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date conversion error for {date_str}: {e}")
            return get_date_only()

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

    def collect_links(self):
        """
        Collect article links from CyberSecurityNews blog and process them with analysis
        """
        print(f"🔗 Starting link collection for {self.name}")
        
        try:
            # Get URL patterns from config - now structured as nested dict
            url_patterns = self.config.get("url_patterns", {})
            
            # Iterate through all configured search terms
            for search_term, term_config in url_patterns.items():
                print(f"🔍 Searching for '{search_term}' articles...")
                
                # Get configuration for this search term
                max_pages = term_config.get("max_pages", 2)
                url_template = term_config.get("url")
                
                print(f"📊 Will search {max_pages} pages for '{search_term}'")
                
                for page_index in range(1, max_pages + 1):
                    page_url = url_template.format(page_index)
                    print(f"📄 Processing page {page_index}: {page_url}")
                    
                    try:
                        # Use requests for initial page loading
                        response = self.session.get(page_url, timeout=30)
                        response.raise_for_status()                 
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Find article blocks - based on your reference code
                        article_blocks = soup.find_all("div", class_="td_module_16 td_module_wrap td-animation-stack")
                        if not article_blocks:
                            print(f"⚠️  No articles found on page {page_index}")
                            continue
                        
                        for article in article_blocks:
                            try:
                                # Extract date - based on your reference code
                                post_date_element = article.find("span", class_="td-post-date")
                                if not post_date_element:
                                    continue
                                    
                                time_element = post_date_element.find("time")
                                if not time_element:
                                    continue
                                
                                post_date = time_element.get('datetime')
                                if not post_date:
                                    continue
                                
                                # Convert date format
                                formatted_date = self.convert_date_format(post_date)
                                
                                # Extract article link
                                link_element = article.find("a")
                                if not link_element:
                                    continue
                                
                                article_link = link_element.get('href')
                                if not article_link:
                                    continue
                                
                                # Use enhanced pipeline processing method with LLM analysis
                                if not self.process_discovered_link_with_analysis(formatted_date, article_link):
                                    # Found duplicate, but continue processing other articles
                                    return
                                
                            except Exception as e:
                                print(f"❌ Error processing article: {e}")
                                continue
                    
                    except Exception as e:
                        print(f"❌ Error processing page {page_index}: {e}")
                        continue
                    
                    # Add delay between pages
                    time.sleep(self.config.get("delay", 1))
        
        except Exception as e:
            print(f"❌ Error in link collection: {e}")
        
        print(f"🎯 Link collection completed. Found {self.stats['links_discovered']} articles")

    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """
        Extract article content from CyberSecurityNews using Selenium
        Based on your reference implementation
        """
        try:
            print(f"🔍 Extracting content from: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".td-post-content.tagdiv-type"))
            )
            # Find the main content container
            article_content = driver.find_element(By.CSS_SELECTOR, ".td-post-content.tagdiv-type")
            # Use ContentExtractor to parse elements
            webpage_content = self.parse_elements(driver, article_content)
            return webpage_content
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete CybersecurityNews crawling pipeline:
        1. Collect links from CybersecurityNews articles page
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        from datetime import datetime
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Starting CybersecurityNews crawler pipeline...")
            
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
            
            self.logger.info(f"✅ CybersecurityNews crawler completed: {self.stats['links_discovered']} discovered, "
                           f"{self.stats['content_saved']} content saved, {self.stats['links_failed']} failed")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"❌ CybersecurityNews crawler failed: {e}"
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
