"""
TuxCare blog crawler - integrated link collection, content extraction and LLM analysis
Uses dynamic WebDriver for both link collection and content extraction
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
from datetime import datetime
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import get_date_only

class TuxCareCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for TuxCare blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "tuxcare")
        ContentExtractor.__init__(self)
        self.config = SOURCES["tuxcare"]
        self.name = "tuxcare"  # Add name attribute for compatibility
        self._content_driver = None
        self._list_driver = None  # Separate driver for browsing article lists
    
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
    
    def collect_links(self) -> int:
        """Collect article links from TuxCare blog using WebDriver"""
        self.logger.info("🔗 Starting TuxCare link collection")
        links_found = 0
        
        try:
            # Use dedicated driver for link collection
            driver = self.get_list_driver()
            driver.get(self.config["url"])
            time.sleep(2)
            
            # Wait for blog posts container to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "blog-posts"))
                )
            except Exception as e:
                self.logger.error(f"Blog posts container not found: {e}")
                return 0
            
            # Find the blog posts container
            blog_container = driver.find_element(By.CLASS_NAME, "blog-posts")
            posts = blog_container.find_elements(By.CLASS_NAME, "post")
            
            if not posts:
                self.logger.warning("No blog posts found")
                return 0
            
            self.logger.info(f"Found {len(posts)} blog posts")
            
            # Process each post
            for item in posts:
                try:
                    # Extract link
                    link_element = item.find_element(By.TAG_NAME, "a")
                    link_url = link_element.get_attribute("href")
                    
                    if not link_url:
                        continue
                    
                    # Ensure absolute URL
                    if not link_url.startswith('http'):
                        link_url = "https://tuxcare.com" + link_url
                    
                    # Extract date
                    post_date_element = item.find_element(By.CLASS_NAME, "post-date").find_element(By.TAG_NAME, "span")
                    datetime_str = post_date_element.get_attribute('outerHTML').replace('<span>', '').replace('</span>', '')
                    
                    # Parse date: format is "Month Day, Year"
                    date_obj = datetime.strptime(datetime_str, "%B %d, %Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    
                    self.logger.info(f"Processing: {link_url} ({formatted_date})")
                    
                    # Process with LLM analysis - returns False if duplicate found
                    if not self.process_discovered_link_with_analysis(formatted_date, link_url):
                        self.logger.info("Stopping due to duplicate detection")
                        break
                    
                    links_found += 1
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    self.logger.error(f"Error processing blog post: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error in link collection: {e}")
        
        self.logger.info(f"🔗 Collected {links_found} links from TuxCare")
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
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from a TuxCare article using WebDriver"""
        try:
            self.logger.info(f"📄 Extracting content from: {url}")
            
            driver = self.get_content_driver()
            driver.get(url)
            time.sleep(3)
            
            # Scroll to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for the main content area to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "tcl-m-content"))
                )
            except Exception as e:
                self.logger.error(f"Content area not found: {e}")
                return None
            
            # Extract article content
            article_content = driver.find_element(By.CLASS_NAME, "tcl-m-content")
            
            # Use ContentExtractor to parse elements
            webpage_content = self.parse_elements(driver, article_content)
            
            if not webpage_content or len(webpage_content.strip()) < 100:
                self.logger.warning(f"No content extracted from {url}")
                return None
                
            return webpage_content
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete TuxCare crawling pipeline:
        1. Collect links from TuxCare blog
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting TuxCare blog crawler pipeline...")
            
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
            
            self.logger.info(f"✅ TuxCare crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ TuxCare crawler failed: {e}"
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
