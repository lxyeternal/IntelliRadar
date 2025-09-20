"""
BleepingComputer Blog crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
Based on BleepingComputer blog structure and pagination
"""

import time
import json
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import normalize_datetime, get_date_only


class BleepingcomputerCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for BleepingComputer blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "bleepingcomputer")
        ContentExtractor.__init__(self)
        self.config = SOURCES["bleepingcomputer"]
        self.name = "bleepingcomputer"  # Add name attribute for compatibility
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

    def collect_links(self) -> int:
        """
        Collect article links from BleepingComputer blog with pagination and process them with analysis
        Based on bleepingcomputer_blog() logic from Collection code
        Returns number of links found
        """
        print(f"🔗 Starting link collection for {self.name}")
        
        links_found = 0
        
        try:
            driver = self.get_list_driver()
            
            # Process pages based on configuration
            max_pages = self.config.get("max_pages", 10)
            
            for page_index in range(1, max_pages):
                try:
                    # Get page URL - first page uses base_url, others use url_patterns
                    if page_index == 1:
                        page_url = self.config.get("base_url", "https://www.bleepingcomputer.com/tag/supply-chain-attack/")
                    else:
                        url_pattern = self.config.get("url_patterns", "https://www.bleepingcomputer.com/tag/supply-chain-attack/page/{}/")
                        page_url = url_pattern.format(page_index)
                    
                    print(f"📄 Processing BleepingComputer page {page_index}/{max_pages - 1}: {page_url}")
                    
                    driver.get(page_url)
                    
                    # Wait for main news container to load and stop loading immediately
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "bc-home-news-main-wrap"))
                    )
                    driver.execute_script("window.stop();")  # Stop loading the rest immediately
                    
                    # Find the main news container
                    bc_latest_news = driver.find_element(By.ID, "bc-home-news-main-wrap")
                    bc_latest_news_items = bc_latest_news.find_elements(By.CLASS_NAME, "bc_latest_news_text")
                    
                    print(f"📊 Found {len(bc_latest_news_items)} news items on page {page_index}")
                    
                    # Process each news item
                    for li_tag in bc_latest_news_items:
                        try:
                            # Extract link (second <a> tag based on Collection logic)
                            a_tag = li_tag.find_element(By.TAG_NAME, "a")
                         
                            li_url = a_tag.get_attribute("href").strip()
                            
                            if not li_url:
                                continue
                            
                            # Extract date from bc_news_date class
                            datetime_str = li_tag.find_element(By.CLASS_NAME, "bc_news_date").text.strip()
                            formatted_date = self.convert_date_format(datetime_str.lower())
                            
                            print(f"bleepingcomputer {formatted_date} {li_url}")
                            
                            # Process the link with analysis
                            if not self.process_discovered_link_with_analysis(formatted_date, li_url):
                                # Duplicate found, but continue processing other articles
                                continue
                            
                            links_found += 1
                            print(f"✅ Processed: {li_url} (date: {formatted_date})")
                            
                        except Exception as item_error:
                            print(f"❌ Error processing news item: {item_error}")
                            continue
                    
                except Exception as page_error:
                    print(f"❌ Error processing page {page_index}: {page_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error in link collection: {e}")
        
        print(f"🎯 Link collection completed. Found {links_found} articles")
        return links_found

    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """
        Extract article content from BleepingComputer using Selenium
        Based on bleepingcomputer_content() logic from Collection code
        """
        try:
            print(f"🔍 Extracting content from: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            time.sleep(10)
            
            # Scroll to bottom to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for the article section to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "article_section"))
                )
            except:
                # If timeout, try to find the element anyway
                pass
            
            # Find the article content section
            article_section = driver.find_element(By.CLASS_NAME, "article_section")
            
            # Use ContentExtractor to parse elements from the content section
            webpage_content = self.parse_elements(driver, article_section)
            return webpage_content
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete BleepingComputer blog crawling pipeline:
        1. Collect links from BleepingComputer blog with pagination
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting BleepingComputer blog crawler pipeline...")
            
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
            
            self.logger.info(f"✅ BleepingComputer blog crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ BleepingComputer blog crawler failed: {e}"
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