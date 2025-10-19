import os
import requests
from typing import List, Dict, NamedTuple
from .logger_config import downloader_logger as logger


class DownloadTask(NamedTuple):
    """Represents a single download task with all required information"""
    version: str
    tarball_url: str
    filename: str
    save_dir: str
    save_path: str


class NPMDownloader:
    """Download NPM package source code"""
    
    def __init__(self, mirrors: Dict[str, str], base_dir: str, settings: Dict = None):
        self.mirrors = mirrors
        self.base_dir = base_dir
        self.settings = settings or {}
        self.timeout = self.settings.get('timeout_seconds', 60)
        
    def download(self, package_name: str, versions: List[str]) -> Dict[str, str]:
        """
        Download NPM package versions
        
        Improved architecture:
        1. Collect all download tasks (versions, URLs, paths)
        2. Filter and validate (skip -security versions, deduplicate)
        3. Execute downloads (create folders only when needed)
        
        Args:
            package_name: Package name (may contain scopes like @scope/package)
            versions: List of versions to download, ["*"] means all versions
            
        Returns:
            Dict mapping version to full file path (only successful downloads)
        """
        # Step 1: Quick check if any requested version is a security placeholder
        if self._all_versions_are_security(versions):
            logger.info(f"Requested versions contain -security placeholder (removed by NPM), skipping entire package: {package_name}")
            return {}
        
        # Step 2: Collect download tasks from registry
        download_tasks = self._collect_download_tasks(package_name, versions)
        
        # Step 3: If no valid tasks, return empty dict (no folders created)
        if not download_tasks:
            logger.warning(f"No valid versions to download for {package_name}")
            return {}
        
        # Step 4: Execute downloads (folders created only here)
        results = self._execute_downloads(download_tasks)
        
        return results
    
    def _collect_download_tasks(self, package_name: str, versions: List[str]) -> List[DownloadTask]:
        """
        Collect all download tasks from registry without creating any folders
        
        Args:
            package_name: Package name
            versions: List of versions to download, ["*"] means all versions
            
        Returns:
            List of DownloadTask objects
        """
        tasks = []
        download_all = "*" in versions
        max_wildcard_versions = self.settings.get('max_wildcard_versions', 10)
        
        for mirror_name, mirror_url in self.mirrors.items():
            package_url = os.path.join(mirror_url, package_name)
            
            try:
                response = requests.get(package_url, timeout=self.timeout)
                if response.status_code != 200:
                    continue
                
                data = response.json()
                versions_data = data.get('versions', {})
                
                if not isinstance(versions_data, dict):
                    continue
                
                # Check if ANY version is a security placeholder (ends with -security)
                if versions_data:
                    available_versions = [v.get('version', k) for k, v in versions_data.items()]
                    if any(v.endswith("-security") for v in available_versions):
                        logger.info(f"Package contains security placeholder versions (removed by NPM), skipping entire package: {package_name}")
                        return []  # Return empty list - no downloads needed for this package
                
                # Sort versions for wildcard downloads (newest first)
                if download_all:
                    version_items = sorted(
                        versions_data.items(),
                        key=lambda x: x[1].get('time', {}).get('modified',
                                     x[1].get('time', {}).get('created', '')),
                        reverse=True
                    )
                else:
                    version_items = versions_data.items()
                
                # Collect valid download tasks
                seen_versions = set()
                collected_count = 0
                
                for version_key, details in version_items:
                    version = details.get('version', version_key)
                    
                    # Skip duplicates
                    if version in seen_versions:
                        continue
                    
                    # This should never happen (already filtered at package level)
                    # But keep as safety check
                    if version.endswith("-security"):
                        logger.warning(f"Found security version that wasn't caught earlier: {version}")
                        continue
                    
                    # Filter by requested versions
                    if not download_all and version not in versions:
                        continue
                    
                    # Apply max_wildcard_versions limit
                    if download_all and collected_count >= max_wildcard_versions:
                        logger.info(f"Reached max wildcard versions limit ({max_wildcard_versions})")
                        break
                    
                    # Get tarball URL
                    tarball_url = details.get('dist', {}).get('tarball')
                    if not tarball_url:
                        continue
                    
                    # Prepare paths (but don't create folders yet)
                    filename = tarball_url.split('/')[-1]
                    save_dir = os.path.join(self.base_dir, 'npm', package_name, version)
                    save_path = os.path.join(save_dir, filename)
                    
                    # Create download task
                    task = DownloadTask(
                        version=version,
                        tarball_url=tarball_url,
                        filename=filename,
                        save_dir=save_dir,
                        save_path=save_path
                    )
                    tasks.append(task)
                    seen_versions.add(version)
                    
                    if download_all:
                        collected_count += 1
                
                # If we collected tasks, break (no need to try other mirrors)
                if tasks:
                    logger.debug(f"Collected {len(tasks)} download tasks for {package_name}")
                    break
                
            except Exception as e:
                logger.warning(f"Error accessing {mirror_name} for {package_name}: {e}")
                continue
        
        return tasks
    
    def _execute_downloads(self, tasks: List[DownloadTask]) -> Dict[str, str]:
        """
        Execute download tasks, creating folders only when needed
        
        Args:
            tasks: List of DownloadTask objects
            
        Returns:
            Dict mapping version to full file path (only successful downloads)
        """
        results = {}
        
        for task in tasks:
            try:
                # Check if file already exists
                if os.path.exists(task.save_path):
                    logger.debug(f"File already exists: {task.save_path}")
                    results[task.version] = task.save_path
                    continue
                
                # Download file
                response = requests.get(task.tarball_url, timeout=self.timeout)
                if response.status_code != 200:
                    logger.error(f"Failed to download {task.version}: HTTP {response.status_code}")
                    continue
                
                # Create directory only now (after successful download)
                os.makedirs(task.save_dir, exist_ok=True)
                
                # Save file
                with open(task.save_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded {task.version} -> {task.save_path}")
                results[task.version] = task.save_path
                
            except Exception as e:
                logger.error(f"Failed to download {task.version}: {e}")
                # Don't add to results on failure
                continue
        
        return results
    
    def _all_versions_are_security(self, versions: List[str]) -> bool:
        """
        Check if any version is a security placeholder (ends with -security)
        
        Args:
            versions: List of version strings
            
        Returns:
            True if any non-wildcard version ends with -security, False otherwise
        """
        # Filter out wildcard markers
        non_wildcard_versions = [v for v in versions if v != "*"]
        
        # If only wildcard, we need to check actual versions from registry
        # So return False here and let the download logic handle it
        if not non_wildcard_versions:
            return False
        
        # Check if ANY non-wildcard version is a security placeholder
        return any(v.endswith("-security") for v in non_wildcard_versions)
    

