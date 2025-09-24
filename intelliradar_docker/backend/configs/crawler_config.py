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
        "url_pattern": "https://snyk.io/blog/?topic=code-security&topic=open-source-security&topic=supply-chain-security&page={}",
        "max_pages": 25,
        "needs_selenium": True
    },
    "github": {
        "name": "GitHub Advisory",
        "url_pattern": {
            "rust": {
                "url": "https://github.com/advisories?page={}&query=type%3Amalware+ecosystem%3Arust",
                "max_pages": 2
            },
            "pypi": {
                "url": "https://github.com/advisories?page={}&query=type%3Amalware+ecosystem%3Apip",
                "max_pages": 2
            },
            "npm": {
                "url": "https://github.com/advisories?page={}&query=type%3Amalware+ecosystem%3Anpm",
                "max_pages": 400
            }
        },
        "needs_selenium": True
    },
    "sonatype": {
        "name": "Sonatype Blog", 
        "url_pattern": "https://www.sonatype.com/blog?category=all&type=all&page={}",
        "max_pages": 17,
        "needs_selenium": False
    },
    "bleepingcomputer": {
        "name": "BleepingComputer",
        "url_patterns": "https://www.bleepingcomputer.com/tag/supply-chain-attack/page/{}/",
        "base_url": "https://www.bleepingcomputer.com/tag/supply-chain-attack/",
        "max_pages": 10,
        "needs_selenium": True
    },
    "medium": {
        "name": "Medium Recommended",
        "url": "https://medium.com/tag/supply-chain-security/recommended",
        "max_scroll": 30,
        "needs_selenium": True,
        "delay": 2
    },
    "checkmarx": {
        "name": "Checkmarx Blog",
        "url": "https://checkmarx.com/blog/",
        "max_load_more": 35,
        "needs_selenium": True
    },
    "socketdev": {
        "name": "Socket Blog",
        "url": "https://socket.dev/blog?page={}",
        "max_pages": 9,
        "needs_selenium": True
    },
    "jfrog": {
        "name": "JFrog Blog",
        "url": "https://jfrog.com/blog",
        "max_pages": 75,
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
        "needs_selenium": True
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
        "url_patterns": [
            "https://securityaffairs.com/tag/npm/page/{}",
            "https://securityaffairs.com/tag/pypi/page/{}"
        ],
        "max_pages": 3,
        "needs_selenium": False,
        "delay": 1,
        "enable_analysis": False
    },
    "cybersecuritynews": {
        "name": "Cyber Security News",
        "url_patterns": {
            "pypi": {
                "url": "https://cybersecuritynews.com/page/{}/?s=pypi",
                "max_pages": 12
            },
            "npm": {
                "url": "https://cybersecuritynews.com/page/{}/?s=npm",
                "max_pages": 22
            }
        },
        "needs_selenium": True,
        "delay": 2,
        "enable_analysis": False
    },
    "rhisac": {
        "name": "RH-ISAC Blog",
        "url_pattern": "https://rhisac.org/blog/page/{}/",
        "max_pages": 20,
        "needs_selenium": False
    },
    "osv": {
        "name": "OSV Malicious Packages",
        "osv_repo_url": "https://github.com/ossf/malicious-packages.git",
        "needs_selenium": False,
        "type": "repository"
    },
    "snykdb": {
        "name": "Snyk Security Database",
        "url_pattern": {
            "npm": "https://security.snyk.io/vuln/npm/{}",
            "pypi": "https://security.snyk.io/vuln/pip/{}"
        },
        "max_pages": 30,
        "needs_selenium": True
    }
}

# Global config instance
config = CrawlerConfig()
