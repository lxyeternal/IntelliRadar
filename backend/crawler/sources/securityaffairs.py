"""
SecurityAffairs crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
import json
import os
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import normalize_datetime, get_date_only


class SecurityaffairsCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for SecurityAffairs blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "securityaffairs")
        ContentExtractor.__init__(self)
        self.config = SOURCES["securityaffairs"]
        self.name = "securityaffairs"  # Add name attribute for compatibility
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
        """Convert SecurityAffairs date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
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
        """Collect and process article links from SecurityAffairs blog pages (both npm and pypi tags)"""
        try:
            processed_count = 0
            url_patterns = self.config.get('url_patterns', [])
            max_pages = self.config.get('max_pages', 3)
            
            if not url_patterns:
                self.logger.error("No URL patterns configured for SecurityAffairs")
                return 0
            
            # Process each URL pattern (npm and pypi)
            for url_pattern in url_patterns:
                self.logger.info(f"Processing URL pattern: {url_pattern}")
                
                # Collect from all pages for this pattern
                for page_index in range(1, max_pages):
                    page_url = url_pattern.format(page_index)
                    self.logger.info(f"Collecting links from page {page_index}: {page_url}")
                    
                    response = self.session.get(page_url)
                    if response.status_code != 200:
                        self.logger.warning(f"Failed to fetch page {page_index}: {response.status_code}")
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find the main news block
                    latest_news_block = soup.find("div", class_="latest-news-block")
                    if not latest_news_block:
                        self.logger.warning(f"No news block found on page {page_index}")
                        continue
                    
                    # Find all article cards
                    article_rows = latest_news_block.find_all("div", class_="news-card news-card-category mb-3 mb-lg-5")
                    
                    if not article_rows:
                        self.logger.warning(f"No articles found on page {page_index}")
                        continue
                    
                    self.logger.info(f"Found {len(article_rows)} articles on page {page_index}")
                    
                    for article in article_rows:
                        try:
                            # Extract publish time
                            post_time = article.find("div", class_="post-time mb-3")
                            if not post_time:
                                continue
                                
                            spans = post_time.find_all("span")
                            if len(spans) < 2:
                                continue
                                
                            datetime_str = spans[1].text.strip().lower()
                            formatted_date = self.convert_date_format(datetime_str)
                            
                            # Extract article link
                            article_link_element = article.find("a")
                            if not article_link_element:
                                continue
                                
                            article_link = article_link_element.get('href')
                            if not article_link:
                                continue
                            
                            # Process the discovered link with analysis
                            if self.process_discovered_link_with_analysis(formatted_date, article_link):
                                processed_count += 1
                                
                        except Exception as e:
                            self.logger.error(f"Error processing article: {e}")
                            continue
                    
                    # Add delay between pages
                    time.sleep(self.config.get('delay', 1))
                
                # Add delay between different URL patterns
                time.sleep(self.config.get('delay', 1))
            
            self.logger.info(f"Processed {processed_count} links from SecurityAffairs (npm + pypi tags)")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"Link collection failed: {e}")
            return 0

    def extract_content(self, url: str) -> Optional[str]:
        """Extract article content from SecurityAffairs using Selenium"""
        driver = None
        try:
            driver = self.get_content_driver()
            
            self.logger.info(f"Extracting content from: {url}")
            driver.get(url)
            time.sleep(3)
            
            # Scroll to load content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for the main content block to load
            content_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".article-details-block.wow.fadeInUp.animated"))
            )
            
            # Extract content using the parse_elements method from ContentExtractor
            content = self.parse_elements(driver, content_element)
            
            if content:
                self.logger.info(f"Successfully extracted content ({len(content)} chars) from {url}")
                return content
            else:
                self.logger.warning(f"No content extracted from {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete SecurityAffairs crawling pipeline:
        1. Collect links from SecurityAffairs blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting SecurityAffairs crawler pipeline...")
            
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
            
            self.logger.info(f"✅ SecurityAffairs crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ SecurityAffairs crawler failed: {e}"
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
        """Clean up resources"""
        self.close_content_driver()
