"""
IntelliRadar Source Code Collector

Collects source code for PyPI and npm packages from threat_intelligence collection.
Only processes packages where source_collected is False or doesn't exist.
Updates source_code.versions and source_collected fields after collection.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from downloader.download_manager import DownloadManager
from database.mongodb_manager import MongoDBStorageManager


class SourceCodeCollector:
    """Collects source code for PyPI and npm packages only"""
    
    SUPPORTED_MANAGERS = ['pypi', 'npm']
    
    def __init__(self, task_logger=None, task_id=None):
        """
        Initialize the source code collector
        
        Args:
            task_logger: Optional TaskLogger instance for logging
            task_id: Optional task ID for logging
        """
        print("\n" + "="*60)
        print("🚀 IntelliRadar Source Code Collector")
        print("="*60)
        
        self.task_logger = task_logger
        self.task_id = task_id
        
        self.db = MongoDBStorageManager()
        self.collection = self.db.db["threat_intelligence"]
        print("✅ Database connected")
        
        self.download_manager = DownloadManager(
            task_logger=task_logger,
            task_id=task_id
        )
        print(f"✅ Download manager initialized")
        print(f"📁 Storage path: {self.download_manager.storage_dir}")
        print("="*60)
    
    def collect_all(self) -> Dict[str, int]:
        """Collect source code for all packages that need it"""
        print("\n" + "="*60)
        print("📊 Starting source code collection")
        print("="*60)
        
        all_packages = list(self.collection.find({}))
        total_count = len(all_packages)
        
        print(f"📦 Total packages in database: {total_count}")
        
        stats = {
            "total_in_db": total_count,
            "pypi_npm_count": 0,
            "already_collected": 0,
            "need_collect": 0,
            "collect_success": 0,
            "collect_failed": 0,
            "other_managers": 0
        }
        
        for idx, package in enumerate(all_packages, 1):
            package_name = package.get('package_name', 'unknown')
            package_manager = package.get('package_manager', 'unknown').lower()
            package_id = package.get('id')
            
            if package_manager not in self.SUPPORTED_MANAGERS:
                stats['other_managers'] += 1
                continue
            
            stats['pypi_npm_count'] += 1
            
            source_collected = package.get('source_collected', False)
            
            if source_collected is True:
                stats['already_collected'] += 1
                continue
            
            stats['need_collect'] += 1
            
            print(f"\n[{idx}/{total_count}] Processing: {package_name} ({package_manager})")
            
            result = self._collect_package_source(package)
            
            if result['success']:
                stats['collect_success'] += 1
                print(f"  ✅ Success: downloaded {result['downloaded_count']} versions")
            else:
                stats['collect_failed'] += 1
                print(f"  ⚠️  Failed or empty: {result['message']}")
        
        self._print_final_stats(stats)
        
        # 记录到任务日志
        if self.task_logger and self.task_id:
            self.task_logger.update_collector_result(self.task_id, stats)
        
        return stats
    
    def _collect_package_source(self, package: Dict) -> Dict:
        """Collect source code for a single package"""
        package_name = package.get('package_name')
        package_manager = package.get('package_manager', 'unknown').lower()
        package_id = package.get('id')
        package_versions = package.get('package_versions', [])
        
        # Skip only if version list is empty
        if not package_versions:
            self._update_database(package_id, {}, success=True)
            return {
                'success': True,
                'message': 'Empty version list, skipped',
                'downloaded_count': 0
            }
        
        try:
            # Let download_manager handle all version types (including wildcards)
            download_results = self.download_manager.download_package(
                package_manager=package_manager,
                package_name=package_name,
                versions=package_versions
            )
            
            # download_results now contains {version: file_path} for successful downloads
            downloaded_versions = download_results
            
            # Always update database as "collected" (even if no versions downloaded)
            self._update_database(package_id, downloaded_versions, success=True)
            
            success_count = len(downloaded_versions)
            total_count = len(download_results)
            
            # Special message for NPM security versions
            if package_manager == 'npm' and total_count == 0 and package_versions:
                message = 'All versions are 0.0.1-security (removed by NPM)'
            elif success_count == 0 and total_count == 0:
                message = 'No versions to download'
            else:
                message = f'Downloaded {success_count}/{total_count} versions'
            
            return {
                'success': success_count > 0,
                'message': message,
                'downloaded_count': success_count
            }
            
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            # Still mark as collected even if exception occurred
            self._update_database(package_id, {}, success=True)
            
            return {
                'success': False,
                'message': f'Download exception: {str(e)}',
                'downloaded_count': 0
            }
    
    def _update_database(self, package_id: str, downloaded_versions: Dict[str, str], 
                        success: bool = True):
        """Update source_code and source_collected fields in database"""
        try:
            update_data = {
                "source_code.versions": downloaded_versions,
                "source_collected": True,
                "source_download_time": datetime.utcnow().isoformat() + "Z"
            }
            
            result = self.collection.update_one(
                {"id": package_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"  ✓ Database updated")
            else:
                print(f"  ⚠️  Database not updated (same value exists)")
                
        except Exception as e:
            print(f"  ❌ Database update failed: {e}")
    
    def _print_final_stats(self, stats: Dict):
        """Print final collection statistics"""
        print("\n" + "="*60)
        print("📊 Source Code Collection Report")
        print("="*60)
        print(f"📦 Total packages: {stats['total_in_db']}")
        print(f"🎯 PyPI/npm packages: {stats['pypi_npm_count']}")
        print(f"⏭️  Other managers: {stats['other_managers']} (skipped)")
        print("-"*60)
        print(f"✅ Already collected: {stats['already_collected']}")
        print(f"🔄 Need collection: {stats['need_collect']}")
        print("-"*60)
        print(f"✅ Collection success: {stats['collect_success']}")
        print(f"⚠️  Collection failed: {stats['collect_failed']}")
        print("="*60)
        
        total_pypi_npm = stats['pypi_npm_count']
        total_collected = stats['already_collected'] + stats['collect_success']
        
        if total_pypi_npm > 0:
            progress = (total_collected / total_pypi_npm) * 100
            print(f"📈 Overall progress: {total_collected}/{total_pypi_npm} ({progress:.1f}%)")
        
        print("="*60)
    
    def get_collection_status(self) -> Dict:
        """Get current collection status for PyPI and npm packages"""
        try:
            total = self.collection.count_documents({})
            
            pypi_count = self.collection.count_documents({"package_manager": "pypi"})
            npm_count = self.collection.count_documents({"package_manager": "npm"})
            
            pypi_collected = self.collection.count_documents({
                "package_manager": "pypi",
                "source_collected": True
            })
            npm_collected = self.collection.count_documents({
                "package_manager": "npm",
                "source_collected": True
            })
            
            pypi_pending = pypi_count - pypi_collected
            npm_pending = npm_count - npm_collected
            
            return {
                "total_packages": total,
                "pypi": {
                    "total": pypi_count,
                    "collected": pypi_collected,
                    "pending": pypi_pending
                },
                "npm": {
                    "total": npm_count,
                    "collected": npm_collected,
                    "pending": npm_pending
                }
            }
        except Exception as e:
            print(f"❌ Failed to get collection status: {e}")
            return {}
    
    def close(self):
        """Close database and download manager connections"""
        if hasattr(self, 'db'):
            self.db.close()
        if hasattr(self, 'download_manager'):
            self.download_manager.close()


def main():
    """Main entry point for standalone execution"""
    print("\n")
    print("🎯 " + "="*58)
    print("🎯 IntelliRadar Source Code Collector")
    print("🎯 " + "="*58)
    print("📝 Collects source code for PyPI and npm packages")
    print("📝 Only processes packages with source_collected=False")
    print("📝 Updates source_code and source_collected fields")
    print("="*62 + "\n")
    
    collector = None
    
    try:
        collector = SourceCodeCollector()
        
        print("\n📊 Current collection status:")
        status = collector.get_collection_status()
        
        if status:
            print(f"  Total packages: {status['total_packages']}")
            print(f"  PyPI: {status['pypi']['collected']}/{status['pypi']['total']} collected, "
                  f"{status['pypi']['pending']} pending")
            print(f"  npm:  {status['npm']['collected']}/{status['npm']['total']} collected, "
                  f"{status['npm']['pending']} pending")
        
        input("\n⚠️  Press Enter to start collection, or Ctrl+C to cancel...")
        
        result = collector.collect_all()
        
        print("\n🎉 Source code collection completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Collection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector:
            collector.close()
            print("\n✅ Database connection closed")


if __name__ == "__main__":
    main()
