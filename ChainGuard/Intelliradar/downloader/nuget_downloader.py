import os
import requests
from typing import List, Dict
from .utils import mkdir


class NuGetDownloader:
    """Download NuGet package source code"""
    
    def __init__(self, mirrors: Dict[str, str], base_dir: str, settings: Dict = None):
        self.mirrors = mirrors
        self.base_dir = base_dir
        self.settings = settings or {'scope_separator': '##'}
        self.timeout = self.settings.get('timeout_seconds', 60)
        
    def download(self, package_name: str, versions: List[str]) -> Dict[str, str]:
        """
        Download NuGet package versions
        
        Args:
            package_name: Package name
            versions: List of versions to download, ["*"] means all versions
            
        Returns:
            Dict mapping version to full file path (only successful downloads)
        """
        results = {}
        download_all = "*" in versions
        scope_separator = self.settings.get('scope_separator', '##')
        safe_package_name = package_name.replace('/', scope_separator)
        
        # Get max wildcard versions limit from settings
        max_wildcard_versions = self.settings.get('max_wildcard_versions', 10)
        
        for mirror_name, mirror_url in self.mirrors.items():
            package_url = mirror_url.format(package_name.lower())
            
            try:
                response = requests.get(package_url, timeout=self.timeout)
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                items_data = data.get('items', [])
                
                if not items_data:
                    continue
                
                versions_data = items_data[0].get('items', [])
                
                # For wildcard downloads, reverse to get newest versions first
                if download_all:
                    versions_data = list(reversed(versions_data))
                
                downloaded_count = 0
                for details in versions_data:
                    version = details.get('catalogEntry', {}).get('version')
                    if not version or version in results:
                        continue
                    
                    if not download_all and version not in versions:
                        continue
                    
                    # Apply max_wildcard_versions limit for wildcard downloads
                    if download_all and downloaded_count >= max_wildcard_versions:
                        print(f"Reached max wildcard versions limit ({max_wildcard_versions}), stopping")
                        break
                    
                    package_url = details.get('packageContent')
                    if not package_url:
                        continue
                    
                    filename = os.path.basename(package_url)
                    file_path = self._download_file(
                        safe_package_name, version, filename,
                        package_url, mirror_name
                    )
                    
                    if file_path:
                        results[version] = file_path
                        if download_all:
                            downloaded_count += 1
                
                if results:
                    break
                    
            except Exception as e:
                print(f"Error accessing {mirror_name} for {package_name}: {e}")
                continue
        
        return results
    
    def _download_file(self, safe_package_name: str, version: str,
                       filename: str, url: str, mirror_name: str) -> str:
        """
        Download single file
        
        Returns:
            Full file path if successful, empty string if failed
        """
        try:
            save_dir = mkdir(self.base_dir, 'nuget', safe_package_name, version)
            save_path = os.path.join(save_dir, filename)
            
            if os.path.exists(save_path):
                print(f"File already exists: {save_path}")
                return save_path
            
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {safe_package_name} {version} from {mirror_name}")
                return save_path
                
        except Exception as e:
            print(f"Failed to download {safe_package_name} {version}: {e}")
        
        return ""

