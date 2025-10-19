"""
XMirror crawler - integrated link collection, content extraction and LLM analysis
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
from bs4 import BeautifulSoup
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from analysis.intelligence_analyzer import IntelligenceAnalyzer
from utils.time_utils import normalize_datetime, get_date_only


class XMirrorCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for XMirror Security Dynamic with link collection, content extraction and LLM analysis"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "xmirror")
        ContentExtractor.__init__(self)
        self.config = SOURCES["xmirror"]
        self.name = "xmirror"  # Add name attribute for compatibility
        self._content_driver = None
        # Statistics tracking
        self.stats = {
            'links_discovered': 0,
            'content_saved': 0,
            'links_processed': 0,
            'links_failed': 0
        }
    
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


    def get_first_article_id(self, driver) -> Optional[int]:
        """
        从页面的 script 标签中提取第一篇文章的真实ID（无需点击跳转）
        Returns: 文章ID，如果失败返回None
        """
        try:
            self.logger.info("🔍 Extracting first article ID from page script...")
            
            # 执行JavaScript来获取页面中的文章数据
            script = """
            // 查找页面中所有的script标签
            var scripts = document.getElementsByTagName('script');
            var results = [];
            for (var i = 0; i < scripts.length; i++) {
                var content = scripts[i].innerHTML;
                if (content && content.length > 50) {
                    // 查找包含Next.js数据推送的脚本
                    if (content.includes('self.__next_f.push') && content.includes('newsList')) {
                        results.push({
                            index: i,
                            content: content,
                            preview: content.substring(0, 300),
                            type: 'nextjs_data'
                        });
                    }
                }
            }
            return results;
            """
            
            results = driver.execute_script(script)
            self.logger.info(f"🔎 Found {len(results)} script(s) containing article data")
            
            if not results:
                self.logger.warning("⚠️ No script tags with article data found")
                return None
            
            # 处理Next.js数据
            for result_item in results:
                self.logger.info(f"📜 Checking script #{result_item['index']} (Next.js data)")
                content = result_item['content']
                
                # 从newsList附近提取第一个4位数ID
                pattern = r'newsList.*?id.*?(\d{4})'
                matches = re.search(pattern, content, re.DOTALL)
                
                if matches:
                    article_id = int(matches.group(1))
                    self.logger.info(f"✅ Successfully extracted first article ID from script: {article_id}")
                    return article_id
            
            self.logger.warning("⚠️ Could not find article ID in script data")
            return None
                
        except Exception as e:
            self.logger.error(f"❌ Error extracting first article ID from script: {e}")
            return None

    def collect_links(self):
        """Collect links from XMirror dynamic pages using Selenium"""
        driver = self.get_content_driver()
        
        # 🆕 只在第一页获取一次起始ID
        first_page_first_article_id = None
        
        try:
            for page_index in range(1, self.config["max_pages"] + 1):
                page_url = self.config["url_pattern"].format(page_index)
                self.logger.info(f"Processing XMirror page {page_index}: {page_url}")
                
                driver.get(page_url)
                
                # Wait for content to load with timeout
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".ListContents_news-item__1bv7j"))
                    )
                except:
                    # If no articles found, log warning and continue to next page
                    self.logger.warning(f"No articles found on page {page_index}")
                    continue
                
                time.sleep(2)
                
                # Find all article elements
                article_elements = driver.find_elements(By.CSS_SELECTOR, ".ListContents_news-item__1bv7j")
                
                # Check if no articles found
                if not article_elements:
                    self.logger.warning(f"No articles found on page {page_index}")
                    continue
                
                self.logger.info(f"Found {len(article_elements)} articles on page {page_index}")
                
                # 🆕 只在第一页时获取起始ID
                if page_index == 1:
                    first_page_first_article_id = self.get_first_article_id(driver)
                    if first_page_first_article_id is None:
                        self.logger.error(f"❌ Failed to get first article ID on page 1, aborting")
                        return  # 如果第一页获取失败，整个爬取终止
                    
                    self.logger.info(f"🎯 First page starting ID: {first_page_first_article_id}")
                
                # Collect all article data first to avoid stale elements
                articles_data = []
                for i, article_element in enumerate(article_elements):
                    try:
                        # Get title with better error handling
                        try:
                            title_elem = article_element.find_element(By.CSS_SELECTOR, "h3.ListContents_title__VIs2W")
                            title_text = title_elem.text.strip() if title_elem.text else "N/A"
                        except:
                            title_text = "N/A"
                        
                        # 🆕 使用第一页的起始ID + 全局位置递减计算
                        # 公式：first_page_first_article_id - (page_index - 1) * articles_per_page - i
                        # 例如：首页第一个ID=100，每页5篇
                        #   Page 1, Article 0: 100 - 0*5 - 0 = 100
                        #   Page 1, Article 1: 100 - 0*5 - 1 = 99
                        #   Page 2, Article 0: 100 - 1*5 - 0 = 95
                        #   Page 2, Article 1: 100 - 1*5 - 1 = 94
                        articles_per_page = len(article_elements)
                        article_id = first_page_first_article_id - (page_index - 1) * articles_per_page - i
                        full_link = f"https://www.xmirror.cn/particulars?type=dt&id={article_id}"
                        
                        self.logger.info(f"Processing article {i+1}/{len(article_elements)} on page {page_index}: ID={article_id}")
                        
                        # Extract date with better error handling using correct selector
                        try:
                            date_elem = article_element.find_element(By.CSS_SELECTOR, ".ListContents_time__cp0NV")
                            date_text = date_elem.text.strip() if date_elem.text else ""
                            date_str = date_text.split()[-1] if date_text else "None"
                        except:
                            date_str = "None"
                        
                        formatted_date = get_date_only(date_str)
                        
                        self.logger.info(f"  Title: {title_text[:50]}{'...' if len(title_text) > 50 else ''}")
                        self.logger.info(f"  Date: {formatted_date}")
                        self.logger.info(f"  URL: {full_link}")
                        
                        # Store article data
                        articles_data.append({
                            'title': title_text,
                            'url': full_link,
                            'date': formatted_date
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"Error collecting article {i+1}: {e}")
                
                # Now process all collected articles
                self.logger.info(f"Starting to process {len(articles_data)} collected articles from page {page_index}")
                for idx, article_data in enumerate(articles_data):
                    try:
                        self.logger.info(f"Processing article {idx+1}/{len(articles_data)}: {article_data['url']}")
                        
                        # Process the link
                        if not self.process_discovered_link_with_analysis(
                            article_data['date'], 
                            article_data['url'], 
                            article_data['title']
                        ):
                            # Duplicate found, stop processing
                            self.logger.info(f"Duplicate found: {article_data['url']} - stopping processing")
                            return
                        
                        self.logger.info(f"Successfully processed article {idx+1}: {article_data['title'][:30]}...")
                        print("xmirror", article_data['date'], article_data['url'])
                        
                    except Exception as e:
                        self.logger.error(f"Error processing article {idx+1}: {e}")
                        continue
                
                self.logger.info(f"📊 Page {page_index} completed: {len(articles_data)} articles processed")
                self.delay()
        
        finally:
            pass
    
    def process_discovered_link_with_analysis(self, post_date: str, url: str, title: str = None) -> bool:
        """
        Enhanced link processing with LLM analysis using unified StorageManager
        Returns False if duplicate found (should stop), True to continue
        """
        self.logger.info(f"🔍 Checking for duplicates: {url}")
        
        # Check if already processed
        if self.storage.is_duplicate(url):
            self.logger.info(f"❌ Duplicate found: {url}")
            return False
        
        self.logger.info(f"✅ New article found, proceeding with content extraction...")
        
        # Update statistics - link discovered
        self.stats['links_discovered'] += 1
        self.stats['links_processed'] += 1
        
        # Extract content
        self.logger.info(f"📄 Extracting content from: {url}")
        content = self.extract_content(url)
        if not content:
            self.logger.warning(f"⚠️ Failed to extract content from {url}")
            # Still save the link even if content extraction failed
            self.logger.info(f"💾 Saving link entry without content...")
            self.storage.save_link_entry(self.name, url, post_date)
            self.stats['links_failed'] += 1
            return True
        
        self.logger.info(f"✅ Content extracted successfully ({len(content)} characters)")
        self.stats['content_saved'] += 1
        
        # Perform LLM analysis
        self.logger.info(f"🤖 Performing LLM analysis for {url}...")
        analyzer = IntelligenceAnalyzer()
        analysis_result = analyzer.analyze_content(content)
        self.logger.info(f"✅ LLM analysis completed")
        
        # Save link with content and analysis results using unified storage
        self.logger.info(f"💾 Saving to database: {url}")
        timestamp = self.storage.save_link_with_analysis(
            self.name, url, post_date, content, analysis_result
        )
        
        self.logger.info(f"🎉 Successfully processed and analyzed: {url} (timestamp: {timestamp})")
        return True
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from XMirror article"""
        try:
            self.logger.info(f"🌐 Navigating to article page: {url}")
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            self.logger.info(f"⏳ Waiting for content to load...")
            # Wait for main content to load using XMirror's specific selector
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "particulars_content__KXqCW"))
            )
            
            self.logger.info(f"🔍 Finding article content container...")
            # Find the article content container
            article_content = driver.find_element(By.CLASS_NAME, "particulars_content__KXqCW")
            
            self.logger.info(f"📝 Parsing article elements...")
            content = self.parse_elements(driver, article_content)
            
            if content:
                self.logger.info(f"✅ Content parsed successfully: {len(content)} characters")
            else:
                self.logger.warning(f"⚠️ No content extracted from article")
                
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting XMirror content from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete XMirror crawling pipeline:
        1. Collect links from XMirror dynamic pages
        2. Extract content from each link
        3. Perform LLM analysis on content
        4. Save everything to storage
        
        Returns:
            dict: Summary of the crawling results
        """
        from datetime import datetime
        start_time = datetime.now()
        
        try:
            self.logger.info("🚀 Starting XMirror crawler pipeline...")
            
            # Step 1: Collect links with integrated content extraction and analysis
            self.collect_links()
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Generate summary with correct field names for TaskLogger
            result = {
                'source': self.name,
                'status': 'success',
                'links_discovered': self.stats['links_discovered'],
                'links_processed': self.stats['links_processed'],
                'content_saved': self.stats['content_saved'],
                'links_failed': self.stats['links_failed'],
                'duration': duration,
                'pipeline_mode': True
            }
            
            self.logger.info(f"✅ XMirror crawler completed: {self.stats['links_discovered']} discovered, "
                           f"{self.stats['content_saved']} content saved, {self.stats['links_failed']} failed")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"❌ XMirror crawler failed: {e}"
            self.logger.error(error_msg)
            return {
                'source': self.name,
                'status': 'failed',
                'links_discovered': self.stats['links_discovered'],
                'links_processed': self.stats['links_processed'],
                'content_saved': self.stats['content_saved'],
                'links_failed': self.stats['links_failed'],
                'duration': duration,
                'error': str(e)
            }
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources after crawling"""
        self.close_content_driver()


if __name__ == "__main__":
    """Main execution block for running the XMirror crawler directly"""
    crawler = XMirrorCrawler()
    try:
        result = crawler.run()
        print(f"\n✅ XMirror crawler completed: {result}")
    except Exception as e:
        print(f"\n❌ XMirror crawler failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.cleanup()