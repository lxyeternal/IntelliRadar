# IntelliRadar Backend Crawler

Simple and clean threat intelligence data collection system.

## Features

- 🚀 **Simple Setup**: Uses `webdriver-manager` for automatic driver management
- 🔄 **Concurrent Processing**: Multi-threaded crawler execution  
- 📊 **Smart Stop Mechanism**: Automatically stops when duplicate URLs found (time-ordered crawling)
- 🎯 **Modular Design**: Easy to add new data sources
- 📋 **18+ Sources**: Complete coverage of major security blogs and threat intel feeds
- 🛡️ **Error Handling**: Robust error handling and logging
- 💡 **Intelligent Parsing**: Different parsers for requests vs Selenium-based sources

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run All Crawlers
```bash
python main.py
```

### 3. Run Specific Sources
```bash
# Run popular sources
python main.py --sources snyk github sonatype

# Run all medium sources
python main.py --sources medium medium_recommand

# Run Chinese sources
python main.py --sources qianxin
```

### 4. Adjust Concurrency
```bash
python main.py --workers 5
```

## Architecture

```
backend/
├── crawler/
│   ├── base.py           # Base crawler classes
│   ├── config.py         # Configuration settings  
│   ├── pipeline.py       # Main coordinator
│   └── sources/          # Source-specific crawlers (18 total)
│       ├── snyk.py       # Snyk security blog
│       ├── github.py     # GitHub security advisories
│       ├── sonatype.py   # Sonatype main blog
│       ├── sonatype_oss.py # Sonatype OSS blog
│       ├── medium.py     # Medium security blogs
│       ├── checkmarx.py  # Checkmarx research
│       ├── socket.py     # Socket security blog
│       ├── jfrog.py      # JFrog security research
│       ├── phylum.py     # Phylum research
│       ├── qianxin.py    # QianXin (Chinese)
│       └── ... (9 more sources)
├── data/
│   ├── links/            # Collected URLs
│   └── content/          # Extracted content
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

## Adding New Sources

1. Create new crawler in `crawler/sources/`:
```python
from ..base import RequestsCrawler

class NewSourceCrawler(RequestsCrawler):
    def __init__(self):
        super().__init__("newsource")
    
    def collect_links(self) -> int:
        # Your crawling logic here
        return links_found
```

2. Register in `pipeline.py`:
```python
self.crawlers = {
    'snyk': SnykCrawler,
    'github': GitHubCrawler,
    'sonatype': SonatypeCrawler,
    'newsource': NewSourceCrawler,  # Add here
}
```

## Data Flow

1. **Link Collection**: Crawlers discover and save URLs to `data/links/waiting.txt`
2. **Deduplication**: URLs are checked against `data/links/collected.txt`
3. **Content Extraction**: Separate process extracts content from waiting URLs
4. **Storage**: Content saved to `data/content/[source]/[timestamp].txt`

## Supported Sources

### 🔒 **Security Blogs & Research**
- **Snyk** - Open source security vulnerabilities
- **GitHub** - Security advisories (malware focus)
- **Checkmarx** - Application security research
- **Socket** - Supply chain security
- **JFrog** - DevOps and container security
- **Phylum** - Package security research

### 🏢 **Vendor Security**
- **Sonatype** - Main blog + OSS focus
- **ReversingLabs** - Threat intelligence
- **Fortinet** - Threat research
- **Check Point** - Intelligence reports
- **Datadog** - Security labs

### 📰 **Security News**
- **BleepingComputer** - PyPI/NPM focus
- **Security Affairs** - General security news
- **Cybersecurity News** - Package manager threats
- **TuxCare** - Linux security
- **RH-ISAC** - Healthcare security

### 🌐 **International**
- **QianXin** - Chinese threat intelligence
- **Medium** - Security community (2 sources)

### 🧠 **Smart Features**
- **Intelligent Stop**: Stops crawling when duplicate URLs detected (time-ordered pages)
- **Dual Parsers**: Uses requests for static content, Selenium for dynamic sites
- **Auto-retry**: Handles temporary failures gracefully
- **Concurrent**: Runs multiple sources simultaneously

## Configuration

Edit `crawler/config.py` to customize:
- Request delays and timeouts
- Directory paths
- Source-specific settings
- Max pages per source
