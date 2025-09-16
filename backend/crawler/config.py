"""
Simple crawler configuration using webdriver-manager
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

@dataclass
class CrawlerConfig:
    """Crawler configuration settings"""
    
    # Base directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Data storage paths
    DATA_DIR: str = os.path.join(BASE_DIR, "backend", "data")
    CONTENT_DIR: str = os.path.join(DATA_DIR, "content")
    LINKS_DIR: str = os.path.join(DATA_DIR, "links")
    
    # Status files
    COLLECTED_LINKS: str = os.path.join(LINKS_DIR, "collected.txt")
    WAITING_LINKS: str = os.path.join(LINKS_DIR, "waiting.txt")
    ERROR_LINKS: str = os.path.join(LINKS_DIR, "errors.txt")
    
    # Crawler settings
    REQUEST_DELAY: float = 1.0
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    def __post_init__(self):
        """Ensure directories exist"""
        Path(self.CONTENT_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.LINKS_DIR).mkdir(parents=True, exist_ok=True)


# Data source configurations - Complete list from original code
SOURCES = {
    "snyk": {
        "name": "Snyk Blog",
        "url_pattern": "https://snyk.io/blog/?tag=open-source-security&page={}",
        "max_pages": 10,
        "needs_selenium": False
    },
    "github": {
        "name": "GitHub Advisory",
        "url_pattern": "https://github.com/advisories?page={}&query=type%3Amalware",
        "max_pages": 30,
        "needs_selenium": True
    },
    "sonatype": {
        "name": "Sonatype Blog", 
        "url_pattern": "https://www.sonatype.com/blog/page/{}",
        "max_pages": 40,
        "needs_selenium": False
    },
    "bleepingcomputer": {
        "name": "BleepingComputer",
        "url_pattern": "https://www.bleepingcomputer.com/tag/pypi/page/{}/",
        "base_url": "https://www.bleepingcomputer.com/tag/npm/",
        "max_pages": 4,
        "needs_selenium": True
    },
    "medium": {
        "name": "Medium Security",
        "url": "https://medium.com/checkmarx-security",
        "max_scroll": 10,
        "needs_selenium": True
    },
    "medium_recommand": {
        "name": "Medium Recommended",
        "url": "https://medium.com/tag/supply-chain-security/recommended",
        "max_scroll": 50,
        "needs_selenium": True
    },
    "checkmarx": {
        "name": "Checkmarx Blog",
        "url": "https://checkmarx.com/blog/",
        "max_load_more": 5,
        "needs_selenium": True
    },
    "socket": {
        "name": "Socket Blog",
        "url": "https://socket.dev/blog",
        "needs_selenium": False
    },
    "jfrog": {
        "name": "JFrog Blog",
        "url": "https://jfrog.com/blog",
        "max_pages": 10,
        "needs_selenium": True
    },
    "tuxcare": {
        "name": "TuxCare Blog",
        "url": "https://tuxcare.com/blog/",
        "needs_selenium": True
    },
    "datadoghq": {
        "name": "Datadog Security Labs",
        "url": "https://securitylabs.datadoghq.com/articles",
        "needs_selenium": True
    },
    "qianxin": {
        "name": "QianXin Blog",
        "url_pattern": "https://tianwen.qianxin.com/blog/page/{}/",
        "base_url": "https://tianwen.qianxin.com/blog/",
        "max_pages": 13,
        "needs_selenium": False
    },
    "phylum": {
        "name": "Phylum Blog",
        "url_pattern": "https://blog.phylum.io/page/{}/",
        "max_pages": 10,
        "needs_selenium": False
    },
    "reversinglabs": {
        "name": "ReversingLabs Blog",
        "url_pattern": "https://www.reversinglabs.com/blog/tag/appsec-supply-chain-security/page/{}/",
        "max_pages": 10,
        "needs_selenium": False
    },
    "checkpoint": {
        "name": "Check Point Research",
        "url_pattern": "https://research.checkpoint.com/intelligence-reports/page/{}/",
        "max_pages": 5,
        "needs_selenium": False
    },
    "fortinet": {
        "name": "Fortinet Threat Research",
        "url": "https://www.fortinet.com/blog/threat-research",
        "max_load_more": 20,
        "needs_selenium": True
    },
    "securityaffairs": {
        "name": "Security Affairs",
        "url_pattern": "https://securityaffairs.com/tag/pypi/page/{}",
        "max_pages": 3,
        "needs_selenium": False
    },
    "rhisac": {
        "name": "RH-ISAC Blog",
        "url_pattern": "https://rhisac.org/blog/page/{}/",
        "max_pages": 20,
        "needs_selenium": False
    },
    "sonatype_oss": {
        "name": "Sonatype OSS Blog",
        "url_pattern": "https://blog.sonatype.com/topic/everything-open-source/page/{}",
        "max_pages": 12,
        "needs_selenium": False
    },
    "cybersecuritynews": {
        "name": "Cybersecurity News",
        "url_pattern": "https://cybersecuritynews.com/page/{}/?s={}",
        "search_terms": ["npm", "pypi"],
        "max_pages": 2,
        "needs_selenium": False
    }
}

# Global config instance
config = CrawlerConfig()
