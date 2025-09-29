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
        """Collect article links from TuxCare blog using WebDriver with pagination"""
        self.logger.info("🔗 Starting TuxCare link collection with pagination")
        links_found = 0
        max_pages = self.config.get("max_pages", 187)
        
        # Initialize analyzer once for all processing
        analyzer = IntelligenceAnalyzer()
        
        try:
            driver = self.get_list_driver()
            
            # Process each page
            for page_num in range(1, max_pages + 1):
                try:
                    # Format URL with page number
                    page_url = self.config["url"].format(page_num)
                    self.logger.info(f"📖 Processing page {page_num}/{max_pages}: {page_url}")
                    
                    driver.get(page_url)
                    time.sleep(3)  # Reduced wait time
                    
                    # Wait for blog posts container to load
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "blog__posts"))
                        )
                    except Exception as e:
                        self.logger.warning(f"Blog posts container not found on page {page_num}: {e}")
                        # Check if this is a 404 or empty page - might indicate end of content
                        if "404" in driver.page_source or "not found" in driver.page_source.lower():
                            self.logger.info(f"Reached end of content at page {page_num}")
                            break
                        continue
                    
                    # Find the blog posts container
                    blog_container = driver.find_element(By.CLASS_NAME, "blog__posts")
                    posts = blog_container.find_elements(By.CLASS_NAME, "blog__post")
                    
                    if not posts:
                        self.logger.warning(f"No blog posts found on page {page_num}")
                        continue
                    
                    self.logger.info(f"Found {len(posts)} blog posts on page {page_num}")
                    
                    # Process each post on this page
                    page_duplicates_found = 0
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
                            try:
                                post_date_element = item.find_element(By.CLASS_NAME, "post_date").text.strip()
                                formatted_date = get_date_only(post_date_element)
                                print("tuxcare", formatted_date, link_url)
                            except Exception as e:
                                self.logger.warning(f"Could not extract date for {link_url}: {e}")
                                formatted_date = datetime.now().strftime('%Y-%m-%d')
                            
                            self.logger.info(f"Processing: {link_url} ({formatted_date})")
                            
                            # Process with shared analyzer instance
                            if not self.process_discovered_link_with_analysis(formatted_date, link_url, analyzer):
                                self.logger.info(f"Duplicate found on page {page_num}")
                                # Don't stop immediately - continue with current page
                                return links_found
                                # continue
                            
                            links_found += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error processing blog post on page {page_num}: {e}")
                            continue
                        
                    self.logger.info(f"✅ Page {page_num} completed: {links_found} total links processed")
                    
                except Exception as e:
                    self.logger.error(f"Error processing page {page_num}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error in link collection: {e}")
        
        # Final statistics
        self.logger.info("="*60)
        self.logger.info(f"🎯 TuxCare Collection Summary:")
        self.logger.info(f"   📄 Pages processed: {min(page_num if 'page_num' in locals() else max_pages, max_pages)}")
        self.logger.info(f"   🔗 Links collected: {links_found}")
        self.logger.info(f"   📊 Average links per page: {links_found / max(1, min(page_num if 'page_num' in locals() else max_pages, max_pages)):.1f}")
        self.logger.info("="*60)
        
        return links_found
    
    def process_discovered_link_with_analysis(self, post_date: str, url: str, analyzer: IntelligenceAnalyzer = None) -> bool:
        """
        Enhanced link processing with LLM analysis using unified StorageManager
        Returns False if duplicate found, True to continue
        """
        # Check if already processed
        if self.storage.is_duplicate(url):
            self.logger.info(f"Duplicate found: {url}")
            return False
        
        # Extract content
        self.logger.info(f"📄 Extracting content from {url}...")
        content = self.extract_content(url)
        if not content:
            self.logger.warning(f"Failed to extract content from {url}")
            # Still save the link even if content extraction failed
            self.storage.save_link_entry(self.name, url, post_date)
            return True
        
        # Perform LLM analysis with shared analyzer
        self.logger.info(f"🤖 Performing LLM analysis for {url}...")
        if analyzer is None:
            analyzer = IntelligenceAnalyzer()
        
        analysis_result = analyzer.analyze_content(content)
        
        # Save link with content and analysis results using unified storage
        timestamp = self.storage.save_link_with_analysis(
            self.name, url, post_date, content, analysis_result
        )
        
        self.logger.info(f"✅ Successfully processed and analyzed: {url} (timestamp: {timestamp})")
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
                'storage_location': 'MongoDB Analysis Collection'
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
