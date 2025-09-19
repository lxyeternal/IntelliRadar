"""
Socket.dev crawler - integrated link collection, content extraction and LLM analysis
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


class SocketCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Socket.dev blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "socketdev")
        ContentExtractor.__init__(self)
        self.config = SOURCES["socketdev"]
        self.name = "socketdev"  # Add name attribute for compatibility
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

    def collect_links(self) -> int:
        """
        Collect article links from Socket.dev blog with pagination and process them with analysis
        Returns number of links found
        """
        print(f"🔗 Starting link collection for {self.name}")
        
        links_found = 0
        
        try:
            # Get base URL from config
            base_url = self.config.get("url", "https://socket.dev/blog")
            print(f"📄 Processing Socket.dev blog with pagination...")
            
            driver = self.get_list_driver()
            
            # Loop through pages based on config
            max_pages = self.config.get("max_pages", 9)
            for page in range(1, max_pages + 1):  # Pages 0 to max_pages
                try:
                    page_url = base_url.format(page)
                    print(f"🔄 Processing page {page}: {page_url}")
                    
                    driver.get(page_url)
                    time.sleep(3)  # Wait for page to load
                    
                    # Wait for articles to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".chakra-linkbox.css-6vqnpm"))
                    )
                    
                    # Find all article containers
                    article_containers = driver.find_elements(By.CSS_SELECTOR, ".chakra-linkbox.css-6vqnpm")
                    
                    if not article_containers:
                        print(f"⚠️  No articles found on page {page}")
                        continue
                    
                    print(f"📊 Found {len(article_containers)} articles on page {page}")
                    
                    for container in article_containers:
                        try:
                            # Extract link using chakra-link chakra-linkbox__overlay
                            link_element = container.find_element(By.CSS_SELECTOR, ".chakra-link.chakra-linkbox__overlay")
                            href = link_element.get_attribute("href")
                            
                            if not href:
                                continue
                            
                            # Build full URL
                            full_url = f"https://socket.dev{href}" if href.startswith("/") else href

                            date_container = container.find_element(By.CSS_SELECTOR, ".css-ld97x4")
                            spans = date_container.find_elements(By.TAG_NAME, "span")
                            
                            if len(spans) > 0:
                                # Get the last span text and clean it
                                date_text = spans[-1].text.strip()
                                date_text = date_text.replace("&nbsp;", "").replace("-", "").strip()
                                formatted_date = self.convert_date_format(date_text)
                                    
                            # Process the link with analysis
                            if not self.process_discovered_link_with_analysis(formatted_date, full_url):
                                # Duplicate found, but continue processing other articles
                                continue
                            links_found += 1
                            print(f"✅ Processed: {full_url} (date: {formatted_date})")
                            
                        except Exception as article_error:
                            print(f"❌ Error processing article: {article_error}")
                            continue
                    
                    # Add delay between pages
                    time.sleep(self.config.get("delay", 1))
                    
                except Exception as page_error:
                    print(f"❌ Error processing page {page}: {page_error}")
                    continue
        
        except Exception as e:
            print(f"❌ Error in link collection: {e}")
        
        print(f"🎯 Link collection completed. Found {links_found} articles")
        return links_found

    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """
        Extract article content from Socket.dev using Selenium
        Based on your reference implementation
        """
        try:
            print(f"🔍 Extracting content from: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for Socket.dev content container to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".prose.css-0"))
            )
            
            # Find the main content container for Socket.dev
            article_content = driver.find_element(By.CSS_SELECTOR, ".prose.css-0")
            
            # Use ContentExtractor to parse elements
            webpage_content = self.parse_elements(driver, article_content)
            return webpage_content
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete Socket.dev crawling pipeline:
        1. Collect links from Socket.dev blog page
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Socket.dev crawler pipeline...")
            
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
            
            self.logger.info(f"✅ Socket.dev crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Socket.dev crawler failed: {e}"
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
