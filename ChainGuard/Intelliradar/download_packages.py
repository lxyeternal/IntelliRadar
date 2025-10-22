#!/usr/bin/env python3
"""
Download malicious packages from aggregated database

Usage:
    # Download all packages from database
    python download_packages.py --from-db
    
    # Download only PyPI packages
    python download_packages.py --from-db --package-manager pypi
    
    # Download specific package
    python download_packages.py --package-manager npm --package-name lodash --versions 1.0.0 1.0.1
    
    # Download all versions of a package
    python download_packages.py --package-manager pypi --package-name requests --versions "*"
    
    # Limit download count
    python download_packages.py --from-db --limit 10
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from downloader.download_manager import main

if __name__ == '__main__':
    main()

