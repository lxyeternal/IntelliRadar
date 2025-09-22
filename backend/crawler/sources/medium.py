"""
Medium Security crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
Based on medium_recommand logic from the reference implementation
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


class MediumCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Medium supply chain security tag with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "medium")
        ContentExtractor.__init__(self)
        self.config = SOURCES["medium"]
        self.name = "medium"  # Add name attribute for compatibility
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
        """
        Convert Medium date format to YYYY-MM-DD format
        Handles three cases:
        1. "2d ago", "3 days ago" -> relative dates
        2. "Sep 9", "Apr 15" -> current year dates  
        3. "Apr 15, 2024" -> specific year dates
        """
        try:
            date_str_clean = date_str.strip()
            date_str_lower = date_str_clean.lower()
            
            # Case 1: Handle relative dates like "2d ago", "3 days ago"
            if "ago" in date_str_lower:
                # Extract number from beginning
                match = re.match(r'(\d+)\s*d', date_str_lower)
                if match:
                    days_ago = int(match.group(1))
                    specific_date = datetime.now() - timedelta(days=days_ago)
                    return specific_date.strftime('%Y-%m-%d')
                
                # Handle "days ago" format
                if "days ago" in date_str_lower:
                    days_ago = int(date_str_lower.split()[0])
                    specific_date = datetime.now() - timedelta(days=days_ago)
                    return specific_date.strftime('%Y-%m-%d')
            
            # Case 2: Handle "Sep 9", "Apr 15" format (current year)
            try:
                specific_date = datetime.strptime(date_str_clean, '%b %d')
                specific_date = specific_date.replace(year=datetime.now().year)
                return specific_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
            
            # Case 3: Handle "Apr 15, 2024" format (with year)
            try:
                specific_date = datetime.strptime(date_str_clean, '%b %d, %Y')
                return specific_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
            
            # Fallback to time_utils if available
            try:
                formatted_date = get_date_only(date_str)
                return formatted_date if formatted_date else "None"
            except:
                return "None"
                
        except Exception as e:
            print(f"⚠️  Date conversion error for '{date_str}': {e}")
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
        Collect article links from Medium supply chain security tag with scrolling and process them with analysis
        Returns number of links found
        """
        print(f"🔗 Starting link collection for {self.name}")
        
        links_found = 0
        
        try:
            # Get base URL from config
            page_url = self.config.get("url", "https://medium.com/tag/supply-chain-security/recommended")
            print(f"📄 Processing Medium page: {page_url}")
            
            driver = self.get_list_driver()
            driver.get(page_url)
            driver.implicitly_wait(10)
            
            # Scroll down to load more articles
            max_scroll = self.config.get("max_scroll", 25)
            print(f"🔄 Scrolling {max_scroll} times to load more articles...")
            
            for count in range(max_scroll):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.get("delay", 2))
                print(f"📜 Scroll {count + 1}/{max_scroll}")
            
            # Wait for articles to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='post-preview']"))
            )
            
            # Find all article containers
            news_blogs = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='post-preview']")
            
            if not news_blogs:
                print(f"⚠️  No articles found")
                return 0
            
            print(f"📊 Found {len(news_blogs)} articles")
            
            for news_blog in news_blogs:
                try:
                    # Extract link from role="link" div's data-href attribute
                    link_div = news_blog.find_element(By.CSS_SELECTOR, "div[role='link'][data-href]")
                    href = link_div.get_attribute("data-href")
                    
                    if not href:
                        continue
                    
                    # Clean URL (remove source parameters)
                    news_url = href.strip().split("?source")[0].strip()
                    
                    # Extract date from specific class structure
                    try:
                        # Find the time container with class="i l" (only first match per article)
                        time_container = news_blog.find_element(By.CSS_SELECTOR, "div.i.l")
                        # Find the time element with class="ac r ly" inside the container
                        datetime_element = time_container.find_element(By.CSS_SELECTOR, ".ac.r.ly")
                        # Get the first span element under this element
                        first_span = datetime_element.find_element(By.TAG_NAME, "span")
                        datetime_str = first_span.text.strip()
                        # Split by newline and take first part if needed
                        datetime_str_clean = datetime_str.split("\n")[0].strip()
                        formatted_date = self.convert_date_format(datetime_str_clean)
                    except Exception as date_error:
                        print(f"⚠️  Error extracting date: {date_error}")
                        # Try alternative time selectors as fallback
                        try:
                            datetime_element = news_blog.find_element(By.CSS_SELECTOR, ".ac.r.ly")
                            # Get the first span element under this element
                            first_span = datetime_element.find_element(By.TAG_NAME, "span")
                            datetime_str = first_span.text.strip()
                            datetime_str_clean = datetime_str.split("\n")[0].strip()
                            formatted_date = self.convert_date_format(datetime_str_clean)
                        except:
                            formatted_date = "None"
                    
                    print(f"medium {formatted_date} {news_url}")
                    
                    # Process the link with analysis
                    if not self.process_discovered_link_with_analysis(formatted_date, news_url):
                        # Duplicate found, but continue processing other articles
                        continue
                    
                    links_found += 1
                    print(f"✅ Processed: {news_url} (date: {formatted_date})")
                    
                except Exception as article_error:
                    print(f"❌ Error processing article: {article_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error in link collection: {e}")
        
        print(f"🎯 Link collection completed. Found {links_found} articles")
        return links_found

    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """
        Extract article content from Medium using Selenium
        Based on your reference implementation
        """
        try:
            print(f"🔍 Extracting content from: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Smooth scroll script from reference
            smooth_scroll_script = """
            let intervalId = setInterval(function() {
                window.scrollBy(0, 200);
            }, 100);

            // Set a timeout to prevent infinite scrolling
            setTimeout(function() {
                clearInterval(intervalId);
            }, 15000); // Stop scrolling after 15 seconds
            """
            # Execute JavaScript script
            driver.execute_script(smooth_scroll_script)
            time.sleep(20)  # Wait for content to load
            
            # Wait for article element to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Find the first article element
            article_element = driver.find_element(By.TAG_NAME, "article")
            
            # Find the first section under the article (this is the main content area)
            content_section = article_element.find_element(By.TAG_NAME, "section")
            
            # Use ContentExtractor to parse elements from the content section
            webpage_content = self.parse_elements(driver, content_section)
            return webpage_content
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete Medium crawling pipeline:
        1. Collect links from Medium supply chain security tag
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Medium crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ Medium crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Medium crawler failed: {e}"
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