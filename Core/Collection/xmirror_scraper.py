#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import Optional


class XMirrorIDExtractor:
    """Extracts article IDs from the XMirror security website (xmirror.cn)."""

    def __init__(self):
        self.setup_logging()
        self.driver = None

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('xmirror_extractor.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Initialize Chrome browser driver."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            driver_path = "/Users/blue/Documents/Github/IntelliRadar/utils/chromedriver/macarm/chromedriver"
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("Chrome driver initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Chrome driver initialization failed: {e}")
            return False

    def extract_first_article_id(self) -> Optional[int]:
        """
        Extract the first article ID from the XMirror dynamic page.
        Returns: Article ID, or None on failure.
        """
        try:
            url = "https://www.xmirror.cn/dynamic?page=1"
            self.logger.info(f"Visiting page: {url}")

            self.driver.get(url)
            time.sleep(8)

            page_title = self.driver.title
            page_url = self.driver.current_url
            self.logger.info(f"Page title: {page_title}")
            self.logger.info(f"Current URL: {page_url}")

            page_source_length = len(self.driver.page_source)
            self.logger.info(f"Page source length: {page_source_length} chars")

            script_count = self.driver.execute_script("return document.getElementsByTagName('script').length;")
            self.logger.info(f"Found {script_count} script tags on page")

            # JavaScript to search all script tags for article data containing newsList or JSON IDs
            script = """
            var scripts = document.getElementsByTagName('script');
            var results = [];
            for (var i = 0; i < scripts.length; i++) {
                var content = scripts[i].innerHTML;
                if (content && content.length > 50) {
                    if (content.includes('self.__next_f.push') && content.includes('newsList')) {
                        results.push({
                            index: i,
                            content: content,
                            preview: content.substring(0, 300),
                            type: 'nextjs_data'
                        });
                    }
                    else if (content.includes('"id":') && (content.includes('list') || content.includes('data'))) {
                        results.push({
                            index: i,
                            content: content,
                            preview: content.substring(0, 200),
                            type: 'json_data'
                        });
                    }
                }
            }
            return results;
            """

            results = self.driver.execute_script(script)
            self.logger.info(f"Found {len(results)} scripts containing IDs")

            if results:
                self.logger.info("Found page data, parsing...")

                nextjs_results = [r for r in results if r.get('type') == 'nextjs_data']
                other_results = [r for r in results if r.get('type') != 'nextjs_data']

                for result_item in nextjs_results:
                    self.logger.info(f"Checking script #{result_item['index']} (Next.js data)")
                    self.logger.info(f"Script preview: {result_item['preview']}")

                    content = result_item['content']
                    article_id = self._extract_nextjs_article_id(content)
                    if article_id:
                        return article_id

                for result_item in other_results:
                    self.logger.info(f"Checking script #{result_item['index']} (JSON data)")
                    self.logger.info(f"Script preview: {result_item['preview']}")

                    content = result_item['content']
                    article_id = self._extract_json_article_id(content)
                    if article_id:
                        return article_id

                self.logger.warning("Could not find article ID in page data")
                return None
            else:
                self.logger.warning("No scripts containing article data found")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting article ID: {e}")
            return None

    def _extract_nextjs_article_id(self, content: str) -> Optional[int]:
        """
        Extract article ID from Next.js data push script.
        Handles patterns like: self.__next_f.push([1,"12:[...{"newsList":{...{"list":[{"id":"3256"...
        """
        try:
            self.logger.info(f"Parsing Next.js data, content length: {len(content)}")

            pattern = r'newsList.*?id.*?(\d{4})'
            matches = re.search(pattern, content, re.DOTALL)

            if matches:
                article_id = int(matches.group(1))
                self.logger.info(f"Successfully extracted article ID from newsList: {article_id}")
                return article_id

            self.logger.warning("Could not find article ID in newsList")
            return None

        except Exception as e:
            self.logger.error(f"Error parsing Next.js data: {e}")
            return None

    def _extract_json_article_id(self, content: str) -> Optional[int]:
        """Extract article ID from plain JSON data."""
        try:
            id_patterns = [
                r'"id"\s*:\s*"(\d+)"',
                r'"id"\s*:\s*(\d+)',
            ]

            for pattern in id_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    article_id = int(matches[0])
                    self.logger.info(f"Extracted article ID from JSON data: {article_id}")
                    return article_id

            return None

        except Exception as e:
            self.logger.error(f"Error parsing JSON data: {e}")
            return None

    def run(self) -> Optional[int]:
        """
        Run the extractor.
        Returns: The extracted article ID.
        """
        try:
            self.logger.info("Starting XMirror article ID extractor")

            if not self.setup_driver():
                return None

            article_id = self.extract_first_article_id()

            if article_id:
                self.logger.info(f"Extraction successful! Article ID: {article_id}")
                return article_id
            else:
                self.logger.error("Extraction failed")
                return None

        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    extractor = XMirrorIDExtractor()
    article_id = extractor.run()

    if article_id:
        print(f"\nExtraction result: {article_id}")
    else:
        print("\nExtraction failed")


if __name__ == "__main__":
    main()
