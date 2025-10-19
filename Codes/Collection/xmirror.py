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
    """
    悬镜安全网站文章ID提取器
    简单提取 https://www.xmirror.cn/dynamic?page=1 页面中第一个文章的ID
    """
    
    def __init__(self):
        """初始化提取器"""
        self.setup_logging()
        self.driver = None
        
    def setup_logging(self):
        """设置日志"""
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
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # 暂时关闭无头模式用于调试
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 使用指定的chromedriver路径
            driver_path = "/Users/blue/Documents/Github/IntelliRadar/utils/chromedriver/macarm/chromedriver"
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("✅ Chrome驱动初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chrome驱动初始化失败: {e}")
            return False
    
    def extract_first_article_id(self) -> Optional[int]:
        """
        从悬镜动态页面提取第一个文章的ID
        Returns: 文章ID，如果失败返回None
        """
        try:
            url = "https://www.xmirror.cn/dynamic?page=1"
            self.logger.info(f"🌐 访问页面: {url}")
            
            self.driver.get(url)
            
            # 等待页面加载并检查状态
            time.sleep(8)
            
            # 检查页面基本信息
            page_title = self.driver.title
            page_url = self.driver.current_url
            self.logger.info(f"📄 页面标题: {page_title}")
            self.logger.info(f"🔗 当前URL: {page_url}")
            
            # 检查页面是否正常加载
            page_source_length = len(self.driver.page_source)
            self.logger.info(f"📏 页面源码长度: {page_source_length} 字符")
            
            # 先检查页面中有多少个script标签
            script_count = self.driver.execute_script("return document.getElementsByTagName('script').length;")
            self.logger.info(f"🔍 页面中共有 {script_count} 个script标签")
            
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
                    // 也查找其他包含文章ID的JSON数据
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
            self.logger.info(f"🔎 找到 {len(results)} 个包含ID的脚本")
            
            if results:
                self.logger.info("✅ 找到页面数据，正在解析...")
                
                # 优先处理Next.js数据
                nextjs_results = [r for r in results if r.get('type') == 'nextjs_data']
                other_results = [r for r in results if r.get('type') != 'nextjs_data']
                
                # 先处理Next.js数据
                for result_item in nextjs_results:
                    self.logger.info(f"📜 检查第 {result_item['index']} 个脚本 (Next.js数据)")
                    self.logger.info(f"🔍 脚本预览: {result_item['preview']}")
                    
                    content = result_item['content']
                    article_id = self._extract_nextjs_article_id(content)
                    if article_id:
                        return article_id
                
                # 再处理其他JSON数据
                for result_item in other_results:
                    self.logger.info(f"📜 检查第 {result_item['index']} 个脚本 (JSON数据)")
                    self.logger.info(f"🔍 脚本预览: {result_item['preview']}")
                    
                    content = result_item['content']
                    article_id = self._extract_json_article_id(content)
                    if article_id:
                        return article_id
                
                self.logger.warning("⚠️ 未能从页面数据中找到文章ID")
                return None
            else:
                self.logger.warning("⚠️ 未找到包含文章数据的脚本")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 提取文章ID时发生错误: {e}")
            return None
    
    def _extract_nextjs_article_id(self, content: str) -> Optional[int]:
        """
        从Next.js数据推送脚本中提取文章ID
        处理类似 self.__next_f.push([1,"12:[...{\"newsList\":{...{\"list\":[{\"id\":\"3256\"...
        """
        try:
            self.logger.info(f"🔍 开始解析Next.js数据，内容长度: {len(content)}")
            
            # 查找newsList附近的第一个4位数ID (经验证有效的方法)
            pattern = r'newsList.*?id.*?(\d{4})'
            matches = re.search(pattern, content, re.DOTALL)
            
            if matches:
                article_id = int(matches.group(1))
                self.logger.info(f"🎯 成功从newsList中提取到文章ID: {article_id}")
                return article_id
            
            self.logger.warning("⚠️ 未能从newsList中找到文章ID")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 解析Next.js数据时出错: {e}")
            return None
    
    def _extract_json_article_id(self, content: str) -> Optional[int]:
        """
        从普通JSON数据中提取文章ID
        """
        try:
            # 使用正则表达式提取第一个文章ID
            # 查找类似 "id":"3256" 或 "id":3256 的模式
            id_patterns = [
                r'"id"\s*:\s*"(\d+)"',  # "id":"3256"
                r'"id"\s*:\s*(\d+)',    # "id":3256
            ]
            
            for pattern in id_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    article_id = int(matches[0])  # 取第一个匹配的ID
                    self.logger.info(f"🎯 从JSON数据中提取到文章ID: {article_id}")
                    return article_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 解析JSON数据时出错: {e}")
            return None
    
    def run(self) -> Optional[int]:
        """
        运行提取器
        Returns: 提取到的文章ID
        """
        try:
            self.logger.info("🚀 启动悬镜文章ID提取器")
            
            # 1. 初始化浏览器
            if not self.setup_driver():
                return None
            
            # 2. 提取文章ID
            article_id = self.extract_first_article_id()
            
            if article_id:
                self.logger.info(f"🎉 提取成功！文章ID: {article_id}")
                return article_id
            else:
                self.logger.error("❌ 提取失败")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 运行过程中发生错误: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔚 浏览器已关闭")


def main():
    """主函数"""
    extractor = XMirrorIDExtractor()
    article_id = extractor.run()
    
    if article_id:
        print(f"\n🎯 提取结果: {article_id}")
    else:
        print("\n❌ 提取失败")


if __name__ == "__main__":
    main()