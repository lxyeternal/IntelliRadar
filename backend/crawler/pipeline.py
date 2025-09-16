"""
Main crawler pipeline coordinator
"""

import logging
import concurrent.futures
from typing import List, Dict
from datetime import datetime

from .sources.snyk import SnykCrawler
from .sources.github import GitHubCrawler
from .sources.sonatype import SonatypeCrawler
from .sources.bleepingcomputer import BleepingComputerCrawler
from .sources.medium import MediumCrawler, MediumRecommandCrawler
from .sources.checkmarx import CheckmarxCrawler
from .sources.socket import SocketCrawler
from .sources.jfrog import JfrogCrawler
from .sources.tuxcare import TuxcareCrawler
from .sources.datadoghq import DatadoghqCrawler
from .sources.qianxin import QianxinCrawler
from .sources.phylum import PhylumCrawler
from .sources.reversinglabs import ReversingLabsCrawler
from .sources.checkpoint import CheckpointCrawler
from .sources.fortinet import FortinetCrawler
from .sources.securityaffairs import SecurityAffairsCrawler
from .sources.rhisac import RhisacCrawler
from .sources.sonatype_oss import SonatypeOssCrawler
from .sources.cybersecuritynews import CybersecurityNewsCrawler


class CrawlerPipeline:
    """Main pipeline for coordinating all crawlers"""
    
    def __init__(self):
        self.logger = logging.getLogger("crawler.pipeline")
        self._setup_logging()
        
        # Available crawlers - Complete list from original code
        self.crawlers = {
            'snyk': SnykCrawler,
            'github': GitHubCrawler,
            'sonatype': SonatypeCrawler,
            'bleepingcomputer': BleepingComputerCrawler,
            'medium': MediumCrawler,
            'medium_recommand': MediumRecommandCrawler,
            'checkmarx': CheckmarxCrawler,
            'socket': SocketCrawler,
            'jfrog': JfrogCrawler,
            'tuxcare': TuxcareCrawler,
            'datadoghq': DatadoghqCrawler,
            'qianxin': QianxinCrawler,
            'phylum': PhylumCrawler,
            'reversinglabs': ReversingLabsCrawler,
            'checkpoint': CheckpointCrawler,
            'fortinet': FortinetCrawler,
            'securityaffairs': SecurityAffairsCrawler,
            'rhisac': RhisacCrawler,
            'sonatype_oss': SonatypeOssCrawler,
            'cybersecuritynews': CybersecurityNewsCrawler
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('crawler.log')
            ]
        )
    
    def run_crawler(self, crawler_name: str, enable_content_processing: bool = True) -> Dict:
        """Run a single crawler"""
        if crawler_name not in self.crawlers:
            return {
                'source': crawler_name,
                'status': 'error',
                'error': f'Unknown crawler: {crawler_name}'
            }
        
        try:
            crawler_class = self.crawlers[crawler_name]
            # Pass content processing flag to crawler
            if hasattr(crawler_class, '__init__'):
                # Try to initialize with content processing flag
                try:
                    crawler = crawler_class()
                    crawler.enable_content_processing = enable_content_processing
                except:
                    crawler = crawler_class()
            else:
                crawler = crawler_class()
            
            return crawler.run()
        except Exception as e:
            return {
                'source': crawler_name,
                'status': 'error',
                'error': str(e)
            }
    
    def run_all(self, max_workers: int = 3, enable_content_processing: bool = True) -> List[Dict]:
        """Run all crawlers concurrently with optional content processing"""
        mode_text = "PIPELINE MODE (Links + Content)" if enable_content_processing else "LINKS ONLY MODE"
        self.logger.info(f"Starting crawler pipeline in {mode_text}")
        start_time = datetime.now()
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all crawler tasks
            future_to_crawler = {
                executor.submit(self.run_crawler, name, enable_content_processing): name 
                for name in self.crawlers.keys()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_crawler):
                result = future.result()
                results.append(result)
                
                status = result.get('status', 'unknown')
                source = result.get('source', 'unknown')
                
                if status == 'success':
                    if enable_content_processing:
                        discovered = result.get('links_discovered', 0)
                        saved = result.get('content_saved', 0)
                        failed = result.get('links_failed', 0)
                        self.logger.info(f"✓ {source}: {discovered} discovered, {saved} content saved, {failed} failed")
                    else:
                        links = result.get('links_discovered', 0)
                        self.logger.info(f"✓ {source}: {links} links collected")
                else:
                    error = result.get('error', 'unknown error')
                    self.logger.error(f"✗ {source}: {error}")
        
        # Summary
        total_time = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results if r.get('status') == 'success')
        
        if enable_content_processing:
            total_discovered = sum(r.get('links_discovered', 0) for r in results if r.get('status') == 'success')
            total_content = sum(r.get('content_saved', 0) for r in results if r.get('status') == 'success')
            total_failed = sum(r.get('links_failed', 0) for r in results if r.get('status') == 'success')
            
            self.logger.info(f"Pipeline completed: {success_count}/{len(results)} sources successful")
            self.logger.info(f"Total links discovered: {total_discovered}")
            self.logger.info(f"Total content saved: {total_content}")
            self.logger.info(f"Total failed: {total_failed}")
        else:
            total_links = sum(r.get('links_discovered', 0) for r in results if r.get('status') == 'success')
            self.logger.info(f"Pipeline completed: {success_count}/{len(results)} sources successful")
            self.logger.info(f"Total links collected: {total_links}")
        
        self.logger.info(f"Total time: {total_time:.2f}s")
        
        return results
    
    def run_sources(self, source_names: List[str], max_workers: int = 3) -> List[Dict]:
        """Run specific crawlers"""
        self.logger.info(f"Starting crawlers: {', '.join(source_names)}")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_crawler = {
                executor.submit(self.run_crawler, name): name 
                for name in source_names if name in self.crawlers
            }
            
            for future in concurrent.futures.as_completed(future_to_crawler):
                result = future.result()
                results.append(result)
        
        return results
