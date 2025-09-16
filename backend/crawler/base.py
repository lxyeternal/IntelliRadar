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

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from .config import config
from .storage import StorageManager


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
    
    def get_driver(self) -> webdriver.Chrome:
        """Get configured Chrome driver using webdriver-manager"""
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
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
                'timestamp': datetime.now().isoformat(),
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
    """Base class for crawlers using Selenium"""
    
    def __init__(self, source_name: str):
        super().__init__(source_name)
        self.driver = None
    
    def start_driver(self):
        """Start Chrome driver"""
        if self.driver is None:
            self.driver = self.get_driver()
    
    def stop_driver(self):
        """Stop Chrome driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_page(self, url: str) -> bool:
        """Navigate to URL with error handling"""
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load page {url}: {e}")
            return False
    
    def run(self) -> Dict[str, any]:
        """Override run to handle driver lifecycle"""
        try:
            self.start_driver()
            return super().run()
        finally:
            self.stop_driver()
