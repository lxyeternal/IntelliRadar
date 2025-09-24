"""
ReversingLabs blog crawler - integrated link collection, content extraction and LLM analysis
Uses static requests for link collection and dynamic WebDriver for content extraction
Integrates IntelligenceAnalyzer for threat intelligence analysis
"""

import time
from typing import Optional
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import get_date_only

class ReversingLabsCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for ReversingLabs blog with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "reversinglabs")
        ContentExtractor.__init__(self)
        self.config = SOURCES["reversinglabs"]
        self.name = "reversinglabs"  # Add name attribute for compatibility
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
    
    def collect_links(self) -> int:
        """Collect article links from ReversingLabs blog pages using static requests"""
        self.logger.info("🔗 Starting ReversingLabs link collection")
        links_found = 0
        
        try:
            for page_index in range(1, 10):  # Pages 1-9 as in original code
                page_url = f"https://www.reversinglabs.com/blog/tag/appsec-supply-chain-security/page/{page_index}/"
                self.logger.info(f"Processing page {page_index}: {page_url}")
                
                try:
                    response = self.session.get(page_url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    if not soup:
                        continue
                    
                    # Find the blog listing container
                    blog_listing_item = soup.find("div", class_="cardflow_cards__cZOG9")
                    if not blog_listing_item:
                        self.logger.warning(f"No blog listing found on page {page_index}")
                        continue
                    
                    # Find all article items
                    article_rows = blog_listing_item.find_all("article", class_="card_card__bn_vJ")
                    if not article_rows:
                        self.logger.warning(f"No articles found on page {page_index}")
                        continue
                    
                    for article in article_rows:
                        try:
                            # Extract datetime - find the suptitle div first, then the time element inside
                            suptitle_element = article.find("div", class_="card_suptitle___bZxs")
                            if not suptitle_element:
                                continue
                            
                            time_element = suptitle_element.find("time")
                            if not time_element:
                                continue
                            
                            datetime_str = time_element.get('datetime')
                            if not datetime_str:
                                continue
                            
                            # Extract article link - look for the "Read More" link or overlay link
                            link_element = article.find("a", class_="card_cont__EYx3B")
                            if not link_element:
                                # Fallback to overlay link
                                link_element = article.find("a", class_="card_overlay__0_PDe")
                            
                            if not link_element:
                                continue
                            
                            article_link = link_element.get('href')
                            if not article_link:
                                continue
                            
                            # Ensure absolute URL
                            if article_link.startswith('/'):
                                article_link = f"https://www.reversinglabs.com{article_link}"
                            
                            # Parse date
                            date_only = get_date_only(datetime_str)
                            
                            # Use enhanced pipeline processing method with LLM analysis
                            if not self.process_discovered_link_with_analysis(date_only, article_link):
                                # Found duplicate, but continue processing other articles
                                continue
                            
                            links_found += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error processing article: {e}")
                            continue
                
                except Exception as e:
                    self.logger.error(f"Error processing page {page_index}: {e}")
                    continue
                
                # Add delay between pages
                time.sleep(1)
        
        except Exception as e:
            self.logger.error(f"Error in link collection: {e}")
        
        self.logger.info(f"🔗 Collected {links_found} links from ReversingLabs")
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
        """Extract content from a ReversingLabs article using WebDriver"""
        try:
            self.logger.info(f"📄 Extracting content from: {url}")
            
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Scroll to bottom to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for the main content element
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "rich-text_richText__UyrDZ"))
                )
            except Exception as e:
                self.logger.warning(f"Timeout waiting for content element: {e}")
                return None
            
            # Extract article content
            article_content = driver.find_element(By.CLASS_NAME, "rich-text_richText__UyrDZ")
            
            # Use ContentExtractor to parse elements
            webpage_content = self.parse_elements(driver, article_content)
            
            if not webpage_content or not webpage_content.strip():
                self.logger.warning(f"No content extracted from {url}")
                return None
                
            return webpage_content
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete ReversingLabs crawling pipeline:
        1. Collect links from ReversingLabs blog
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting ReversingLabs blog crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ ReversingLabs crawler completed successfully: {links_found} links processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ ReversingLabs crawler failed: {e}"
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
