"""
Malicious package source code downloader

Download malicious packages from various package managers for analysis.
Supported: npm, pypi, maven, go, rubygems, nuget
"""

from .download_manager import DownloadManager
from .pypi_downloader import PyPIDownloader
from .npm_downloader import NPMDownloader
from .nuget_downloader import NuGetDownloader

__all__ = [
    'DownloadManager',
    'PyPIDownloader', 
    'NPMDownloader',
    'NuGetDownloader'
]

