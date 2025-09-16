"""
QianXin blog crawler - uses requests for Chinese security blog
Now supports pipeline mode: discover links + extract content immediately
"""

from typing import Optional
from ..base import RequestsCrawler
from ..config import SOURCES
from ..content_extractor import SourceContentExtractor


class QianxinCrawler(RequestsCrawler):
    """Crawler for QianXin security blog"""
    
    def __init__(self):
        super().__init__("qianxin")
        self.config = SOURCES["qianxin"]
        self.content_extractor = SourceContentExtractor()
    
    def collect_links(self) -> int:
        """Collect links from QianXin blog pages"""
        links_found = 0
        
        for page_index in range(1, self.config["max_pages"] + 1):
            if page_index == 1:
                page_url = self.config["base_url"]
            else:
                page_url = self.config["url_pattern"].format(page_index)
            
            soup = self.get_soup(page_url)
            if not soup:
                continue
            
            try:
                recent_post_items = soup.find_all("article", class_="recent-post-item")
                
                for item in recent_post_items:
                    try:
                        # Extract date
                        time_elem = item.find('time', class_='time')
                        if not time_elem:
                            continue
                        formatted_date = time_elem.get('datetime')
                        
                        # Extract link
                        link_elem = item.find("a", class_="title")
                        if not link_elem:
                            continue
                        href_value = link_elem.get('href')
                        full_link = "https://tianwen.qianxin.com" + href_value
                        
                        # Use new pipeline processing method
                        if not self.process_discovered_link(formatted_date, full_link, self.extract_content):
                            # Found duplicate, stop this page
                            return links_found
                        links_found += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error parsing QianXin item: {e}")
            
            except Exception as e:
                self.logger.error(f"Error processing QianXin page {page_index}: {e}")
            
            self.delay()
        
        return links_found
    
    def extract_content(self, url: str) -> Optional[str]:
        """Extract content from QianXin blog article using shared content extractor"""
        return self.content_extractor.extract_qianxin_content(url)
    
    def test_content_extraction(self, test_url: str = None):
        """测试内容提取功能，直接打印提取的内容"""
        if not test_url:
            # 使用默认测试URL - QianXin的一篇文章
            test_url = "https://tianwen.qianxin.com/blog/articles/cyber-threat-intelligence-201812/"
        
        print(f"🧪 测试 QianXin 内容提取")
        print(f"📄 测试URL: {test_url}")
        print("=" * 60)
        
        try:
            # 直接调用内容提取方法
            content = self.extract_content(test_url)
            
            if content:
                print("✅ 内容提取成功!")
                print(f"📊 内容长度: {len(content)} 字符")
                print("-" * 60)
                print("📝 提取的内容:")
                print(content)
                print("-" * 60)
                print("🎉 测试完成!")
            else:
                print("❌ 内容提取失败 - 返回空内容")
                
        except Exception as e:
            print(f"💥 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


# 测试函数 - 可以直接运行
def test_qianxin_crawler():
    """独立的测试函数，可以直接运行"""
    print("🚀 启动 QianXin 爬虫测试...")
    
    crawler = QianxinCrawler()
    
    # 测试内容提取
    crawler.test_content_extraction()


if __name__ == "__main__":
    # 如果直接运行这个文件，会执行测试
    test_qianxin_crawler()