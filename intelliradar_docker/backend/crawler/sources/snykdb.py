"""
Snyk Security Database crawler - integrated link collection and structured data extraction
Extracts structured vulnerability data from Snyk Security Database
Saves data directly as JSON without LLM analysis
"""

import time
import json
import os
from pathlib import Path
from typing import Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import RequestsCrawler
from configs.crawler_config import SOURCES
from ..content_extractor import ContentExtractor
from utils.time_utils import normalize_datetime, get_date_only


class SnykDBCrawler(RequestsCrawler, ContentExtractor):
    """Integrated crawler for Snyk Security Database with structured data extraction"""
    
    def __init__(self):
        RequestsCrawler.__init__(self, "snykdb")
        ContentExtractor.__init__(self)
        self.config = SOURCES["snykdb"]
        self.name = "snykdb"  # Add name attribute for compatibility
        self._content_driver = None
        self._list_driver = None
        
        # Extract URL patterns and package managers from config
        self.url_patterns = self.config["url_pattern"]
        self.max_pages = self.config["max_pages"]
    
    def get_content_driver(self):
        """Get or create a dedicated WebDriver for content extraction"""
        if self._content_driver is None:
            self._content_driver = super().get_content_driver()
            self._content_driver.implicitly_wait(5)
        return self._content_driver
    
    def get_list_driver(self):
        """Get or create a dedicated WebDriver for browsing vulnerability lists"""
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
        """Convert Snyk date format using unified time_utils function"""
        try:
            formatted_date = get_date_only(date_str)
            return formatted_date
        except Exception:
            return "None"
    
    def collect_links(self) -> int:
        """Collect vulnerability links from Snyk Security Database"""
        links_found = 0
        
        for package_manager in self.url_patterns:
            self.logger.info(f"Collecting {package_manager} vulnerabilities from Snyk...")
            package_manager_stopped = False  # 标记当前包管理器是否因重复而停止
            
            for page_index in range(1, self.max_pages + 1):
                if package_manager_stopped:  # 如果当前包管理器已停止，跳出页面循环
                    break
                    
                page_url = self.url_patterns[package_manager].format(page_index)
                
                try:
                    driver = self.get_list_driver()
                    driver.get(page_url)
                    driver.implicitly_wait(10)
                    
                    # Wait for vulnerability table to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "vulns-table"))
                    )
                    
                    vulns_table = driver.find_element(By.CLASS_NAME, "vulns-table")
                    table_tbody = vulns_table.find_element(By.CLASS_NAME, "vulns-table__table")
                    vue_table_rows = table_tbody.find_elements(By.TAG_NAME, "tr")
                    
                    if not vue_table_rows:
                        self.logger.info(f"No vulnerabilities found on page {page_index} for {package_manager}")
                        break
                    
                    page_links = 0
                    for row in vue_table_rows:
                        try:
                            row_tds = row.find_elements(By.TAG_NAME, "td")
                            
                            if len(row_tds) < 3:
                                continue
                            
                            # Extract vulnerability type and link from first column
                            vuln_link_td = row_tds[0]
                            vuln_link_type = vuln_link_td.text.split("\n")[1].strip()
                            vuln_link = vuln_link_td.find_element(By.TAG_NAME, "a").get_attribute('href')
                            if "malicious" not in vuln_link_type.lower():
                                continue
                            
                            # Extract package name from the first 'a' element in the second column
                            try:
                                package_name = row_tds[1].find_element(By.TAG_NAME, "a").text.strip()
                            except:
                                package_name = row_tds[1].text.strip()  # fallback to text content
                            
                            # Extract publish date from third column
                            date_td = row_tds[-1]
                            date_text = date_td.text.strip()
                            formatted_date = self.convert_date_format(date_text)
                            
                            # Process the discovered vulnerability link
                            if not self.process_discovered_link_with_structured_data(formatted_date, vuln_link, package_manager, package_name):
                                # Found duplicate, stop this package manager and move to next
                                self.logger.info(f"Stopping {package_manager} collection - found duplicate, later entries will also be duplicates")
                                package_manager_stopped = True
                                break
                            
                            links_found += 1
                            page_links += 1
                            
                            self.logger.info(f"Processed {package_manager} vulnerability: {vuln_link}")
                            
                        except Exception as e:
                            self.logger.warning(f"Error parsing Snyk vulnerability row: {e}")
                    
                    self.logger.info(f"Page {page_index}/{package_manager}: {page_links} vulnerabilities processed")
                    
                    # Add delay between pages
                    self.delay()
                    
                except Exception as e:
                    self.logger.error(f"Error processing Snyk {package_manager} page {page_index}: {e}")
                    break
            
            self.logger.info(f"✅ {package_manager} package manager completed")
        
        return links_found
    
    def process_discovered_link_with_structured_data(self, post_date: str, url: str, manager: str, package_name: str) -> bool:
        """
        Snyk-specific link processing with structured data extraction
        Returns False if duplicate found (should stop), True to continue
        """
        # Check if already processed
        if self.storage.is_duplicate(url):
            self.logger.info(f"Duplicate found: {url}")
            return False
        
        # Extract structured data from Snyk vulnerability page
        structured_data = self.extract_snyk_structured_data(url, manager, package_name, post_date)
        if not structured_data:
            self.logger.warning(f"Failed to extract structured data from {url}")
            # Still save the link even if data extraction failed
            self.storage.save_link_entry(self.name, url, post_date)
            return True
        
        # Use Storage's method to save the vulnerability data as timestamped JSON
        timestamp = self.storage.save_snyk_vulnerability_data(url, post_date, structured_data)
        
        self.logger.info(f"Successfully processed Snyk vulnerability: {url} (timestamp: {timestamp})")
        return True
    
    def extract_snyk_structured_data(self, url: str, manager: str, package_name: str, post_date: str) -> Optional[Dict]:
        """Extract structured data from Snyk vulnerability page"""
        try:
            driver = self.get_content_driver()
            driver.implicitly_wait(5)
            driver.get(url)
            
            # Wait for main vulnerability page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "vuln-page__body-wrapper"))
            )
            
            # Initialize structured data
            structured_data = {
                "url": url,
                "package_manager": manager,
                "package_name": package_name,  # Use package name from link collection
                "package_versions": "",
                "vulnerability_type": "",
                "fix_method": "",
                "overview": "",
                "behavior": "",
                "references": "",
                "update_date": "",
                "post_date": post_date,  # Add post date from link collection
                "ref_links": []
            }
            
            # Extract package versions from vuln-page__heading
            try:
                vuln_page_heading = driver.find_element(By.CLASS_NAME, "vuln-page__heading")
                vuln_versions = vuln_page_heading.find_element(By.CLASS_NAME, "vuln-versions")
                structured_data["package_versions"] = vuln_versions.text.strip()
            except Exception as e:
                self.logger.debug(f"Error extracting package versions: {e}")
            
            vuln_page_body_wrapper = driver.find_element(By.CLASS_NAME, "vuln-page__body-wrapper")
            left_div = vuln_page_body_wrapper.find_element(By.CLASS_NAME, "left")
            
            # Extract content from markdown sections based on text content
            try:
                markdown_sections = left_div.find_elements(By.CLASS_NAME, "markdown-section")
                
                for section in markdown_sections:
                    try:
                        # Get the full text content of the section
                        heading_text = section.find_element(By.CLASS_NAME, "heading").text.strip()
                        # Check for different content types based on keywords in text
                        if "How to fix" in heading_text:
                            # Extract content from vue--prose
                            try:
                                content = section.find_element(By.CLASS_NAME, "prose").text.strip()
                                structured_data["fix_method"] = content
                            except:
                                pass
                                
                        elif "Overview" in heading_text:
                            try:
                                content = section.find_element(By.CLASS_NAME, "prose").text.strip()
                                structured_data["overview"] = content
                            except:
                                pass
                                
                        elif "Behavior" in heading_text or "Behaviour" in heading_text:
                            try:
                                content = section.find_element(By.CLASS_NAME, "prose").text.strip()
                                structured_data["behavior"] = content
                            except:
                                pass
                                
                        elif "References" in heading_text:
                            # For references, extract both content and links using li elements
                            try:
                                content = section.find_element(By.CLASS_NAME, "prose").text.strip()
                                structured_data["references"] = content
                                
                                # Extract reference links from li elements
                                ref_links = []
                                li_tags = section.find_elements(By.TAG_NAME, "li")
                                for li_tag in li_tags:
                                    try:
                                        link_element = li_tag.find_element(By.TAG_NAME, "a")
                                        link_text = link_element.text.strip()
                                        link_href = link_element.get_attribute("href")
                                        if link_text and link_href:
                                            ref_links.append({
                                                "text": link_text,
                                                "url": link_href
                                            })
                                    except:
                                        # If no link, just add text content
                                        text_content = li_tag.text.strip()
                                        if text_content:
                                            ref_links.append({
                                                "text": text_content,
                                                "url": ""
                                            })
                                
                                if ref_links:
                                    structured_data["ref_links"] = ref_links
                                    
                            except Exception as e:
                                self.logger.debug(f"Error extracting references: {e}")
                                
                    except Exception as e:
                        self.logger.debug(f"Error processing markdown section: {e}")
                        
            except Exception as e:
                self.logger.warning(f"Error extracting markdown sections: {e}")
            
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"Error extracting Snyk structured data from {url}: {e}")
            return None
    
    def run(self) -> dict:
        """
        Main method to execute the complete Snyk Security Database crawling pipeline:
        1. Collect vulnerability links from pip and npm pages (max 30 pages each)
        2. Extract structured data from each vulnerability
        3. Save data as timestamped verify JSON files
        
        Returns:
            dict: Summary of the crawling results
        """
        try:
            self.logger.info("🚀 Starting Snyk Security Database crawler pipeline...")
            
            # Step 1: Collect links with integrated structured data extraction
            links_found = self.collect_links()
            
            # Generate summary
            result = {
                'source': self.name,
                'links_found': links_found,
                'status': 'success',
                'storage_location': 'MongoDB Analysis Collection'
            }
            
            self.logger.info(f"✅ Snyk crawler completed successfully: {links_found} vulnerabilities processed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Snyk crawler failed: {e}"
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

