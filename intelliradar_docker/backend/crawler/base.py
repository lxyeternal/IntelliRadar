"""
Base crawler class with common functionality
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Callable
from pathlib import Path
import os
import sys

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# Removed webdriver_manager import - using local chromedriver instead
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from configs.crawler_config import config
from utils.time_utils import get_current_collected_at

# Support both file-based and MongoDB storage
try:
    from database.mongodb_manager import MongoDBStorageManager as StorageManager  # MongoDB version
    print("🍃 Using MongoDB storage")
except ImportError:
    from .storage import StorageManager  # File-based fallback
    print("📁 Using file-based storage")


class BaseCrawler(ABC):
    """Base class for all crawlers"""
    
    def __init__(self, source_name: str, enable_content_processing: bool = True):
        self.source_name = source_name
        self.logger = logging.getLogger(f"crawler.{source_name}")
        self._setup_logging()
        
        # Initialize storage manager
        self.storage = StorageManager()
        
        # Pipeline mode: process content immediately after finding links
        self.enable_content_processing = enable_content_processing
        
        # Load existing URLs to avoid duplicates
        self._collected_urls = self.storage.load_existing_links(source_name)
        
        # Statistics
        self.stats = {
            'links_discovered': 0,
            'links_processed': 0,
            'links_failed': 0,
            'content_saved': 0
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    
    def is_url_collected(self, url: str) -> bool:
        """Check if URL was already collected"""
        return url in self._collected_urls
    
    def process_discovered_link(self, date: str, url: str, content_extractor: Optional[Callable] = None) -> bool:
        """
        Pipeline processing: check if new, save link, and optionally process content immediately
        Returns False if already collected (signal to stop)
        """
        if self.is_url_collected(url):
            self.logger.debug(f"URL already collected: {url}")
            return False
            
        # Update statistics
        self.stats['links_discovered'] += 1
        self._collected_urls.add(url)
        
        # Process content immediately if enabled
        if self.enable_content_processing and content_extractor:
            try:
                content = content_extractor(url)
                if content:
                    # Save both link and content using storage manager
                    timestamp = self.storage.save_link_entry(
                        source=self.source_name,
                        url=url,
                        post_date=date,
                        content=content
                    )
                    self.stats['content_saved'] += 1
                    self.logger.info(f"✓ Content processed for: {url} -> {timestamp}")
                else:
                    # Save link only, mark content extraction as failed
                    self.storage.save_link_entry(
                        source=self.source_name,
                        url=url,
                        post_date=date
                    )
                    self.stats['links_failed'] += 1
                    self.logger.warning(f"✗ Content extraction failed: {url}")
                    
                self.stats['links_processed'] += 1
                
            except Exception as e:
                # Save link only, log error
                self.storage.save_link_entry(
                    source=self.source_name,
                    url=url,
                    post_date=date
                )
                self.stats['links_failed'] += 1
                self.logger.error(f"✗ Error processing {url}: {e}")
        else:
            # Links-only mode or no content extractor
            self.storage.save_link_entry(
                source=self.source_name,
                url=url,
                post_date=date
            )
            self.logger.info(f"New link discovered: {url}")
        
        return True
    
    def save_link_only(self, date: str, url: str) -> bool:
        """Legacy method: Save discovered link without processing content"""
        if self.is_url_collected(url):
            self.logger.info(f"URL already collected, stopping: {url}")
            return False
            
        self.storage.save_link_entry(
            source=self.source_name,
            url=url,
            post_date=date
        )
        
        self._collected_urls.add(url)
        self.logger.info(f"Saved new link: {url}")
        return True
    
    def get_session(self) -> requests.Session:
        """Get configured requests session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        return session
    
    def get_link_driver(self) -> webdriver.Chrome:
        """Get configured Chrome driver for link collection using local chromedriver"""
        options = Options()
        options.add_argument("--headless")  # 链接抓取使用无头模式
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # Use local chromedriver
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(current_dir, "../drivers/macos/chromedriver")
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        return driver
    
    def get_content_driver(self) -> webdriver.Chrome:
        """Get configured Chrome driver for content extraction using local chromedriver"""
        options = Options()
        # 内容抓取可以不用无头模式，方便调试
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # Use local chromedriver
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(current_dir, "../drivers/macos/chromedriver")
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        return driver
    
    def parse_date(self, date_str: str) -> str:
        """Parse and normalize date string"""
        try:
            # Try common date formats
            for fmt in ["%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"]:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # If parsing fails, return as-is
            return date_str.strip()
            
        except Exception:
            return "None"
    
    def delay(self):
        """Add delay between requests"""
        time.sleep(config.REQUEST_DELAY)
    
    @abstractmethod
    def collect_links(self) -> int:
        """Collect links from this source. Returns number of links found."""
        pass
    
    def extract_content(self, url: str) -> Optional[str]:
        """
        Extract content from a URL. Override this method in subclasses 
        to provide content extraction functionality.
        """
        return None
    
    def run(self) -> Dict[str, any]:
        """Run the crawler and return results"""
        start_time = datetime.now()
        self.logger.info(f"Starting {self.source_name} crawler")
        
        try:
            links_count = self.collect_links()
            
            result = {
                'source': self.source_name,
                'status': 'success',
                'links_discovered': self.stats['links_discovered'],
                'links_processed': self.stats['links_processed'], 
                'links_failed': self.stats['links_failed'],
                'content_saved': self.stats['content_saved'],
                'duration': (datetime.now() - start_time).total_seconds(),
                'timestamp': get_current_collected_at(),
                'pipeline_mode': self.enable_content_processing
            }
            
            if self.enable_content_processing:
                self.logger.info(f"✓ {self.source_name}: {self.stats['links_discovered']} discovered, "
                               f"{self.stats['content_saved']} content saved, {self.stats['links_failed']} failed")
            else:
                self.logger.info(f"✓ {self.source_name}: {links_count} links collected")
            
            return result
            
        except Exception as e:
            result = {
                'source': self.source_name,
                'status': 'error',
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(f"Error in {self.source_name}: {e}")
            return result


class RequestsCrawler(BaseCrawler):
    """Base class for crawlers using requests library"""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
        self.session = self.get_session()
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object for URL"""
        try:
            response = self.session.get(url, timeout=config.TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to get soup for {url}: {e}")
            return None


class SeleniumCrawler(BaseCrawler):
    """Base class for crawlers using Selenium with separate drivers for links and content"""
    
    def __init__(self, source_name: str, enable_content_processing: bool = True):
        super().__init__(source_name, enable_content_processing)
        self.link_driver = None      # 专门用于链接抓取的driver
        self.content_driver = None   # 专门用于内容抓取的driver
    
    def start_link_driver(self):
        """Start Chrome driver for link collection"""
        if self.link_driver is None:
            self.link_driver = self.get_link_driver()
            self.logger.info("🔗 Link collection driver started")
    
    def stop_link_driver(self):
        """Stop Chrome driver for link collection"""
        if self.link_driver:
            self.link_driver.quit()
            self.link_driver = None
            self.logger.info("🔗 Link collection driver stopped")
    
    def start_content_driver(self):
        """Start Chrome driver for content extraction"""
        if self.content_driver is None:
            self.content_driver = self.get_content_driver()
            self.logger.info("📄 Content extraction driver started")
    
    def stop_content_driver(self):
        """Stop Chrome driver for content extraction"""
        if self.content_driver:
            self.content_driver.quit()
            self.content_driver = None
            self.logger.info("📄 Content extraction driver stopped")
    
    def get_link_page(self, url: str) -> bool:
        """Navigate to URL using link driver with error handling"""
        try:
            if self.link_driver is None:
                self.start_link_driver()
            self.link_driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load page with link driver {url}: {e}")
            return False
    
    def get_content_page(self, url: str) -> bool:
        """Navigate to URL using content driver with error handling"""
        try:
            if self.content_driver is None:
                self.start_content_driver()
            self.content_driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load page with content driver {url}: {e}")
            return False
    
    def run(self) -> Dict[str, any]:
        """Override run to handle both drivers lifecycle"""
        try:
            # 启动链接抓取driver
            self.start_link_driver()
            
            # 如果启用内容处理，也启动内容driver
            if self.enable_content_processing:
                self.start_content_driver()
            
            return super().run()
        finally:
            # 确保两个driver都被正确关闭
            self.stop_link_driver()
            self.stop_content_driver()
