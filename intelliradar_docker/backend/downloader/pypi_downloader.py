import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .utils import mkdir
from .logger_config import get_logger

logger = get_logger(__name__)


class PyPIDownloader:
    """Download PyPI package source code"""
    
    def __init__(self, mirrors: Dict[str, str], base_dir: str, settings: Dict = None):
        self.mirrors = mirrors
        self.base_dir = base_dir
        self.settings = settings or {
            'simple_path': 'simple',
            'valid_extensions': ['.tar.gz', '.zip', '.whl'],
            'strip_suffixes': ['-py3-none-any', '-py2.py3-none-any', '.tar.gz', '.zip', '.whl']
        }
        self.timeout = self.settings.get('timeout_seconds', 60)
        
    def download(self, package_name: str, versions: List[str]) -> Dict[str, str]:
        """
        Download PyPI package versions
        
        Args:
            package_name: Package name
            versions: List of versions to download, ["*"] means all versions
            
        Returns:
            Dict mapping version to full file path (only successful downloads)
        """
        results = {}
        download_all = "*" in versions
        
        # Get max wildcard versions limit from settings
        max_wildcard_versions = self.settings.get('max_wildcard_versions', 10)
        
        for mirror_name, mirror_url in self.mirrors.items():
            simple_path = self.settings.get('simple_path', 'simple')
            package_url = os.path.join(mirror_url, simple_path, package_name)
            
            try:
                response = requests.get(package_url, timeout=self.timeout)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a')
                
                if not links:
                    continue
                
                # Group files by version and select best format for each version
                version_files = {}  # {version: [(priority, filename, url), ...]}
                
                for link_tag in links:
                    link_href = link_tag.get('href')
                    filename = link_tag.text.lower()
                    
                    if not self._is_valid_package_file(filename):
                        continue
                    
                    version = self._extract_version(package_name, filename)
                    if not version:
                        continue
                    
                    if not download_all and version not in versions:
                        continue
                    
                    # Get file priority (lower is better)
                    priority = self._get_file_priority(filename)
                    download_url = self._normalize_url(mirror_url, link_href)
                    
                    if version not in version_files:
                        version_files[version] = []
                    version_files[version].append((priority, filename, download_url))
                
                # For wildcard downloads, sort versions by newest first
                if download_all:
                    # Sort version keys in reverse order (newest first)
                    sorted_versions = sorted(version_files.keys(), reverse=True)
                else:
                    sorted_versions = version_files.keys()
                
                downloaded_count = 0
                for version in sorted_versions:
                    # Apply max_wildcard_versions limit for wildcard downloads
                    if download_all and downloaded_count >= max_wildcard_versions:
                        logger.info(f"Reached max wildcard versions limit ({max_wildcard_versions}), stopping")
                        break
                    
                    # Select the best file (lowest priority number)
                    best_file = min(version_files[version], key=lambda x: x[0])
                    priority, filename, download_url = best_file
                    
                    file_path = self._download_file(
                        package_name, version, filename, download_url, mirror_name
                    )
                    
                    if file_path:
                        results[version] = file_path
                        if download_all:
                            downloaded_count += 1
                        
                if results:
                    break
                    
            except Exception as e:
                logger.warning(f"Error accessing {mirror_name}: {e}")
                continue
        
        return results
    
    def _is_valid_package_file(self, filename: str) -> bool:
        """Check if file is a valid package distribution"""
        valid_extensions = self.settings.get('valid_extensions', ['.tar.gz', '.zip', '.whl'])
        return filename.endswith(tuple(valid_extensions))
    
    def _get_file_priority(self, filename: str) -> int:
        """
        Get file format priority (lower is better)
        Priority: .tar.gz (0) > .zip (1) > .whl (2)
        """
        if filename.endswith('.tar.gz'):
            return 0
        elif filename.endswith('.zip'):
            return 1
        elif filename.endswith('.whl'):
            return 2
        else:
            return 999  # Unknown format, lowest priority
    
    def _extract_version(self, package_name: str, filename: str) -> str:
        """Extract version from filename"""
        try:
            version = filename.replace(package_name + '-', '')
            strip_suffixes = self.settings.get('strip_suffixes', [
                '-py3-none-any', '-py2.py3-none-any', '.tar.gz', '.zip', '.whl'
            ])
            for suffix in strip_suffixes:
                version = version.replace(suffix, '')
            return version if version != package_name else None
        except:
            return None
    
    def _normalize_url(self, base_url: str, href: str) -> str:
        """Normalize download URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('../../'):
            return base_url + href.replace('../../', '')
        else:
            return base_url + href
    
    def _download_file(self, package_name: str, version: str, 
                       filename: str, url: str, mirror_name: str) -> str:
        """
        Download single file and clean up lower priority files
        
        Returns:
            Full file path if successful, empty string if failed
        """
        try:
            save_dir = os.path.join(self.base_dir, 'pypi', package_name, version)
            save_path = os.path.join(save_dir, filename)
            
            # Check if this exact file already exists
            if os.path.exists(save_path):
                logger.debug(f"File already exists: {save_path}")
                # Clean up other files with lower priority
                self._cleanup_lower_priority_files(save_dir, filename)
                return save_path
            
            # Check if a higher priority file already exists in the directory
            if os.path.exists(save_dir):
                current_priority = self._get_file_priority(filename)
                for existing_file in os.listdir(save_dir):
                    existing_priority = self._get_file_priority(existing_file)
                    if existing_priority < current_priority:
                        logger.debug(f"Higher priority file already exists: {existing_file}, skipping {filename}")
                        # Return the existing higher priority file path
                        return os.path.join(save_dir, existing_file)
            
            # Download the file
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                # Only create directory when download is successful
                os.makedirs(save_dir, exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded {package_name} {version} from {mirror_name}")
                
                # Clean up lower priority files after successful download
                self._cleanup_lower_priority_files(save_dir, filename)
                return save_path
                
        except Exception as e:
            logger.error(f"Failed to download {package_name} {version}: {e}")
        
        return ""
    
    def _cleanup_lower_priority_files(self, directory: str, keep_filename: str):
        """Remove files with lower priority than the kept file"""
        try:
            keep_priority = self._get_file_priority(keep_filename)
            
            for filename in os.listdir(directory):
                if filename == keep_filename:
                    continue
                
                file_priority = self._get_file_priority(filename)
                if file_priority > keep_priority:
                    file_path = os.path.join(directory, filename)
                    os.remove(file_path)
                    logger.debug(f"Removed lower priority file: {filename}")
        except Exception as e:
            logger.warning(f"Warning: Failed to cleanup files: {e}")

