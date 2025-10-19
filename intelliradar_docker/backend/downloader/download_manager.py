import os
import json
import sys
from typing import Dict, List, Optional
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from .logger_config import downloader_logger as logger

# Try to import MongoDB manager, but make it optional
try:
    from database.mongodb_manager import MongoDBStorageManager
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("MongoDB not available. Database operations will be disabled.")

from .pypi_downloader import PyPIDownloader
from .npm_downloader import NPMDownloader
from .nuget_downloader import NuGetDownloader


class DownloadManager:
    """Unified download manager for malicious packages"""
    
    def __init__(self, config_path: str = None, storage_dir: str = None, 
                 task_logger=None, task_id: str = None):
        """
        Initialize download manager
        
        Args:
            config_path: Path to download_config.json
            storage_dir: Directory to store downloaded packages
            task_logger: Optional TaskLogger instance for logging to database
            task_id: Optional task ID for logging
        """
        self.task_logger = task_logger
        self.task_id = task_id
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../configs/download_config.json'
            )
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        if storage_dir is None:
            base_dir = self.config.get('storage', {}).get('base_dir', 'packages')
            # If base_dir is relative, resolve it relative to the project root (/app in Docker)
            if not os.path.isabs(base_dir):
                # Project root is one level up from downloader directory
                project_root = os.path.dirname(os.path.dirname(__file__))
                storage_dir = os.path.join(project_root, base_dir)
            else:
                storage_dir = base_dir
        
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Merge download settings with package-specific settings
        download_settings = self.config.get('download_settings', {})
        
        pypi_settings = {**download_settings, **self.config.get('pypi_settings', {})}
        npm_settings = {**download_settings, **self.config.get('npm_settings', {})}
        nuget_settings = {**download_settings, **self.config.get('nuget_settings', {})}
        
        self.downloaders = {
            'pypi': PyPIDownloader(
                self.config['pypi_mirrors'], 
                self.storage_dir,
                pypi_settings
            ),
            'npm': NPMDownloader(
                self.config['npm_mirrors'],
                self.storage_dir,
                npm_settings
            ),
            'nuget': NuGetDownloader(
                self.config['nuget_mirrors'],
                self.storage_dir,
                nuget_settings
            ),
        }
        
        # Initialize MongoDB manager only if available
        if MONGODB_AVAILABLE:
            try:
                self.db_manager = MongoDBStorageManager()
            except Exception as e:
                logger.warning(f"Failed to connect to MongoDB: {e}")
                self.db_manager = None
        else:
            self.db_manager = None
        
        logger.info(f"Download manager initialized, storage: {self.storage_dir}")
    
    def download_package(self, package_manager: str, package_name: str, 
                        versions: List[str]) -> Dict[str, str]:
        """
        Download specific package versions
        
        Args:
            package_manager: Package manager (pypi, npm, maven, go, rubygems, nuget)
            package_name: Package name
            versions: List of versions, ["*"] means all versions
            
        Returns:
            Dict mapping version to full file path (only successful downloads)
        """
        package_manager = package_manager.lower()
        
        if package_manager not in self.downloaders:
            logger.error(f"Unsupported package manager: {package_manager}")
            return {}
        
        downloader = self.downloaders[package_manager]
        
        logger.info(f"Downloading {package_manager} package: {package_name}, Versions: {versions}")
        
        results = downloader.download(package_name, versions)
        
        success_count = len(results)
        logger.info(f"Download completed: {success_count} versions succeeded for {package_name}")
        
        # 记录每个下载结果到数据库
        if self.task_logger and self.task_id:
            for version, file_path in results.items():
                self.task_logger.add_download_log(
                    task_id=self.task_id,
                    package_manager=package_manager,
                    package_name=package_name,
                    version=version,
                    status='success',
                    file_path=file_path
                )
        
        return results
    
    def download_from_database(self, package_manager: Optional[str] = None,
                               limit: Optional[int] = None):
        """
        Download packages from aggregated database
        
        Args:
            package_manager: Filter by package manager, None for all
            limit: Maximum number of packages to download
        """
        if not self.db_manager:
            logger.error("Database is not available. Cannot download from database.")
            return
        
        try:
            from database.intelliradar.aggregated_packages import AggregatedPackages
            
            aggregated_collection = self.db_manager.db[AggregatedPackages.collection_name]
            
            query = {}
            if package_manager:
                query['package_manager'] = package_manager.lower()
            
            cursor = aggregated_collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
            
            packages = list(cursor)
            total = len(packages)
            
            logger.info(f"Found {total} packages to download")
            
            stats = {
                'total': total,
                'success': 0,
                'failed': 0,
                'by_manager': {}
            }
            
            for idx, package in enumerate(packages, 1):
                pkg_manager = package.get('package_manager', '').lower()
                pkg_name = package.get('package_name', '')
                pkg_versions = package.get('package_versions', [])
                
                if not pkg_manager or not pkg_name:
                    logger.warning(f"[{idx}/{total}] Skipping invalid package data")
                    stats['failed'] += 1
                    continue
                
                if not pkg_versions:
                    pkg_versions = ['*']
                
                logger.info(f"[{idx}/{total}] Processing: {pkg_manager}/{pkg_name}")
                
                results = self.download_package(pkg_manager, pkg_name, pkg_versions)
                
                if results:
                    stats['success'] += 1
                    stats['by_manager'][pkg_manager] = stats['by_manager'].get(pkg_manager, 0) + 1
                else:
                    stats['failed'] += 1
            
            self._print_stats(stats)
            
        except Exception as e:
            logger.exception(f"Error downloading from database: {e}")
    
    def _print_stats(self, stats: Dict):
        """Print download statistics"""
        logger.info("=" * 60)
        logger.info("DOWNLOAD STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total packages: {stats['total']}")
        logger.info(f"Successfully downloaded: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info("By package manager:")
        for manager, count in sorted(stats['by_manager'].items()):
            logger.info(f"  {manager}: {count}")
        logger.info("=" * 60)
    
    def close(self):
        """Close database connection"""
        if self.db_manager:
            self.db_manager.close()


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download malicious packages')
    parser.add_argument('--package-manager', '-pm', 
                       help='Package manager (pypi, npm, nuget)')
    parser.add_argument('--package-name', '-pn',
                       help='Package name')
    parser.add_argument('--versions', '-v', nargs='+',
                       help='Versions to download, use * for all')
    parser.add_argument('--from-db', action='store_true',
                       help='Download from aggregated database')
    parser.add_argument('--limit', type=int,
                       help='Limit number of packages to download')
    
    args = parser.parse_args()
    
    manager = DownloadManager()
    
    try:
        if args.from_db:
            manager.download_from_database(
                package_manager=args.package_manager,
                limit=args.limit
            )
        elif args.package_name and args.package_manager:
            versions = args.versions or ['*']
            manager.download_package(
                args.package_manager,
                args.package_name,
                versions
            )
        else:
            parser.print_help()
    
    finally:
        manager.close()


if __name__ == '__main__':
    main()

