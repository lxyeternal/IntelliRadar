"""
JFrog Security Blog crawler - integrated link collection, content extraction and LLM analysis
Uses ContentExtractor base class for content extraction functionality
Integrates IntelligenceAnalyzer for threat intelligence analysis
Based on JFrog blog structure and pagination
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


class JfrogCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for JFrog security blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "jfrog")
        ContentExtractor.__init__(self)
        self.config = SOURCES["jfrog"]
        self.name = "jfrog"  # Add name attribute for compatibility
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
        Collect article links from JFrog security blog with pagination and process them with analysis
        Returns number of links found
        """
        print(f"🔗 Starting link collection for {self.name}")
        
        links_found = 0
        
        try:
            # Get base URL from config
            page_url = self.config.get("url", "https://jfrog.com/blog/")
            print(f"📄 Processing JFrog blog page: {page_url}")
            
            driver = self.get_list_driver()
            driver.get(page_url)
            driver.implicitly_wait(10)
            
            # Process current page and navigate through pagination
            max_pages = self.config.get("max_pages", 10)
            current_page = 0
            
            while current_page < max_pages:
                try:
                    print(f"📄 Processing page {current_page + 1}/{max_pages}")
                    
                    # Wait for posts container to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "posts-wrap"))
                    )
                    
                    # Scroll to bottom to ensure all content is loaded
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Find all blog posts on current page
                    posts_wrap = driver.find_element(By.CLASS_NAME, "posts-wrap")
                    blog_posts = posts_wrap.find_elements(By.CSS_SELECTOR, ".col-md-6.blog-post-title")
                    
                    print(f"📊 Found {len(blog_posts)} posts on page {current_page + 1}")
                    
                    # Process each blog post
                    for blog_post in blog_posts:
                        try:
                            # Extract date
                            post_date_element = blog_post.find_element(By.CLASS_NAME, "blog-post-date")
                            post_date_text = post_date_element.text.split()[:3]  # Take first 3 parts
                            date_str = ' '.join(post_date_text).lower()
                            formatted_date = self.convert_date_format(date_str)
                            
                            # Extract link
                            blog_post_link = blog_post.find_element(By.TAG_NAME, "a").get_attribute("href")
                            
                            if not blog_post_link:
                                continue
                            
                            print(f"jfrog {formatted_date} {blog_post_link}")
                            
                            # Process the link with analysis
                            if not self.process_discovered_link_with_analysis(formatted_date, blog_post_link):
                                # Duplicate found, but continue processing other articles
                                return links_found
                            
                            links_found += 1
                            print(f"✅ Processed: {blog_post_link} (date: {formatted_date})")
                            
                        except Exception as post_error:
                            print(f"❌ Error processing blog post: {post_error}")
                            continue
                    
                    # Try to navigate to next page
                    current_page += 1
                    if current_page < max_pages:
                        try:
                            # Scroll to ensure the next button is visible
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(2)
                            
                            # Find and click next button
                            next_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, ".next a"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView();", next_button)
                            driver.execute_script("arguments[0].click();", next_button)
                            
                            # Wait for new page to load
                            time.sleep(10)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "posts-wrap"))
                            )
                            
                        except Exception as nav_error:
                            print(f"⚠️ Navigation error or reached last page: {nav_error}")
                            break
                    
                except Exception as page_error:
                    print(f"❌ Error processing page {current_page + 1}: {page_error}")
                    break
                    
        except Exception as e:
            print(f"❌ Error in link collection: {e}")
        
        print(f"🎯 Link collection completed. Found {links_found} articles")
        return links_found

    def extract_content(self, url: str, driver=None) -> Optional[str]:
        """
        Extract article content from JFrog blog using Selenium
        Based on JFrog blog structure with entry-content class
        """
        try:
            print(f"🔍 Extracting content from: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            time.sleep(5)
            
            # Scroll to bottom to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Wait for the main content area to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "entry-content"))
            )
            
            # Find the article content section
            article_section = driver.find_element(By.CLASS_NAME, "entry-content")
            
            # Use ContentExtractor to parse elements from the content section
            webpage_content = self.parse_elements(driver, article_section)
            return webpage_content
            
        except Exception as e:
            print(f"❌ Error extracting content from {url}: {e}")
            return None

    def run(self) -> dict:
        """
        Main method to execute the complete JFrog blog crawling pipeline:
        1. Collect links from JFrog security blog with pagination
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting JFrog blog crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ JFrog blog crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ JFrog blog crawler failed: {e}"
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