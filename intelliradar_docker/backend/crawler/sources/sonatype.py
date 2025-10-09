"""
Sonatype crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
import json
import os
import re
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


class SonatypeCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Sonatype blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "sonatype")
        ContentExtractor.__init__(self)
        self.config = SOURCES["sonatype"]
        self.name = "sonatype"  # Add name attribute for compatibility
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
        """Convert Sonatype date format using unified time_utils function"""
        try:
            # Use unified time_utils function to normalize date
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self) -> int:
        """Collect links from Sonatype blog pages"""
        links_found = 0
        
        base_url = self.config["url_pattern"]
        max_pages = self.config["max_pages"]
        # Iterate through pages 1-17 based on new Sonatype blog structure
        for page_index in range(1, max_pages + 1):
            # Use url_pattern from config
            page_url = base_url.format(page_index)
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                # Find all resource card content containers
                resource_card_contents = soup.find_all(class_='resource-card__content')
                self.logger.debug(f"Found {len(resource_card_contents)} resource-card__content elements on page {page_index}")
                
                if not resource_card_contents:
                    self.logger.info(f"No resource-card__content found on page {page_index}, stopping")
                    break
                
                # Process each resource card content
                for card_content in resource_card_contents:
                    try:
                        # Find the link in content-body__title
                        title_elem = card_content.find(class_='content-body__title')
                        if not title_elem:
                            continue
                            
                        a_tag = title_elem.find('a')
                        if not a_tag:
                            continue
                            
                        news_href = a_tag.get('href', '').strip()
                        if not news_href:
                            continue
                        
                        # Make URL absolute if needed
                        if news_href.startswith('/'):
                            full_link = "https://www.sonatype.com" + news_href
                        elif news_href.startswith('http'):
                            full_link = news_href
                        else:
                            continue
                        
                        # Set date as None for now (will be extracted during content extraction)
                        formatted_date = "None"
                        
                        # Use enhanced pipeline processing method with LLM analysis
                        if not self.process_discovered_link_with_analysis(formatted_date, full_link):
                            # Found duplicate, continue with other articles
                            return links_found
                        links_found += 1
                        
                        # Print progress (date will be updated during processing)
                        print("sonatype", "processing...", full_link)
                        
                    except Exception as e:
                        self.logger.warning(f"Error parsing Sonatype resource card: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing Sonatype page {page_index}: {e}")
            
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
        
        # Extract date from the article page (since it wasn't available during link collection)
        if post_date == "None":
            extracted_date = self.extract_date(url)
            post_date = extracted_date
        
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
        
        self.logger.info(f"Successfully processed and analyzed: {url} (timestamp: {timestamp}) with date: {post_date}")
        return True
    
    def extract_date(self, url: str) -> str:
        """Extract date from Sonatype blog article page"""
        try:
            driver = self.get_content_driver()
            driver.get(url)
            
            # Look for content-meta__date class with time element
            try:
                date_element = driver.find_element(By.CLASS_NAME, "content-meta__date")
                datetime_attr = date_element.get_attribute("datetime")
                if datetime_attr:
                    # Parse datetime attribute (e.g., "2025-09-17 15:00:00")
                    formatted_date = self.convert_date_format(datetime_attr)
                    return formatted_date
                
                # Fallback: get text content from strong tag inside time element
                strong_elem = date_element.find_element(By.TAG_NAME, "strong")
                if strong_elem:
                    date_text = strong_elem.text.strip()
                    formatted_date = self.convert_date_format(date_text)
                    return formatted_date
                    
            except Exception as e:
                self.logger.debug(f"Could not extract date from content-meta__date: {e}")
            
            return "None"
            
        except Exception as e:
            self.logger.warning(f"Error extracting date from {url}: {e}")
            return "None"

    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from Sonatype blog article"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to load all content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Find the main content in span with id hs_cos_wrapper_post_body
            article_content = None
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "hs_cos_wrapper_post_body")))
                article_content = driver.find_element(By.ID, "hs_cos_wrapper_post_body")
                self.logger.debug("Found content using ID: hs_cos_wrapper_post_body")
            except Exception as e:
                self.logger.warning(f"Could not find main content element: {e}")
                return None
            
            if article_content:
                content = self.parse_elements(driver, article_content)
                return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting Sonatype content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Sonatype crawling pipeline:
        1. Collect links from Sonatype blog pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Sonatype crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ Sonatype crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Sonatype crawler failed: {e}"
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
