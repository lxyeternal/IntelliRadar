"""
Phylum crawler - integrated link collection, content extraction and LLM analysis
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


class PhylumCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Phylum blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "phylum")
        ContentExtractor.__init__(self)
        self.config = SOURCES["phylum"]
        self.name = "phylum"  # Add name attribute for compatibility
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
        """Convert Phylum date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self) -> int:
        """Collect links from Phylum blog pages"""
        links_found = 0
        
        # Iterate through pages 1-10 based on original logic
        base_url = self.config["url_pattern"]
        max_pages = self.config["max_pages"]
        for page_index in range(1, max_pages + 1):
            # Use url_pattern from config
            page_url = base_url.format(page_index)
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                # Find article blocks using exact selectors from original working code
                latest_news_block = soup.find_all("article", class_=["post tag-research", "post tag-insights", "post tag-research featured"])
                
                if not latest_news_block:
                    self.logger.info(f"No more articles found on page {page_index}, stopping")
                    break
                
                # Process articles (skip first one like in original code)
                for article in latest_news_block[1:]:
                    try:
                        # Extract article link using original selector
                        link_elem = article.find("a", class_="post-title-link")
                        if not link_elem:
                            continue
                            
                        article_link = link_elem.get('href')
                        if not article_link:
                            continue
                        
                        # Extract date
                        time_element = article.find("time")
                        if time_element:
                            date_info = time_element.get('datetime') or time_element.get_text(strip=True)
                            formatted_date = self.convert_date_format(date_info)
                        else:
                            formatted_date = "None"
                        
                        # Make URL absolute
                        if not article_link.startswith('http'):
                            full_link = "https://blog.phylum.io" + article_link
                        else:
                            full_link = article_link
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, full_link):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                        
                        # Print progress
                        print("phylum", formatted_date, full_link)
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing Phylum item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Phylum page {page_index}: {e}")
            
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
        """Extract content from Phylum blog article using Ghost CMS structure"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for main content to load using exact selector from original code
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gh-content.gh-canvas")))
            article_content = driver.find_element(By.CSS_SELECTOR, ".gh-content.gh-canvas")
            
            if article_content:
                content = self.parse_elements(driver, article_content)
                return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting Phylum content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Phylum crawling pipeline:
        1. Collect links from Phylum blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Phylum crawler pipeline...")
            
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
            
            self.logger.info(f"✅ Phylum crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Phylum crawler failed: {e}"
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
