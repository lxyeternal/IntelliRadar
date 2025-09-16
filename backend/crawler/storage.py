"""
Storage Manager for IntelliRadar Crawler
Handles unified data storage for links and content
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
import threading


class StorageManager:
    """Unified storage manager for crawler data"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.links_file = self.base_dir / "all_links.json"  # 统一的JSON文件
        self.content_dir = self.base_dir / "content"
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread lock for safe JSON file operations
        self._lock = threading.Lock()
        
        # Initialize links file if it doesn't exist
        if not self.links_file.exists():
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
    
    def generate_timestamp(self) -> str:
        """Generate unique timestamp in format: YYYYMMDD_HHMMSS_microseconds"""
        current_time = datetime.now()
        return current_time.strftime("%Y%m%d_%H%M%S_%f")
    
    def load_existing_links(self, source: str) -> Set[str]:
        """Load existing links for a source to avoid duplicates"""
        with self._lock:
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
                
                source_data = all_data.get(source, [])
                return set(item['url'] for item in source_data)
            except Exception:
                return set()
    
    def save_link_entry(self, source: str, url: str, post_date: str, 
                       timestamp: Optional[str] = None, content: Optional[str] = None) -> str:
        """Save a single link entry and optionally its content"""
        if timestamp is None:
            timestamp = self.generate_timestamp()
        
        # Prepare link entry
        entry = {
            "timestamp": timestamp,
            "source": source,
            "post_date": post_date,
            "url": url,
            "collected_at": datetime.now().isoformat(),
            "content_file": f"{timestamp}.txt" if content else None
        }
        
        # Save link entry to unified JSON file
        with self._lock:
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except Exception:
                all_data = {}
            
            # Ensure source key exists
            if source not in all_data:
                all_data[source] = []
            
            # Add new entry
            all_data[source].append(entry)
            
            # Save back to file
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        # Save content if provided to source-specific folder
        if content:
            self.save_content(source, timestamp, content)
        
        return timestamp
    
    def save_content(self, source: str, timestamp: str, content: str):
        """Save content to text file in source-specific folder"""
        source_content_dir = self.content_dir / source
        source_content_dir.mkdir(exist_ok=True)
        
        content_file = source_content_dir / f"{timestamp}.txt"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_source_stats(self, source: str) -> Dict:
        """Get statistics for a source"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            source_data = all_data.get(source, [])
            total_links = len(source_data)
            with_content = sum(1 for item in source_data if item.get('content_file'))
            latest = max(source_data, key=lambda x: x['collected_at'])['collected_at'] if source_data else None
            
            return {
                "total_links": total_links,
                "with_content": with_content,
                "latest_collection": latest
            }
        except Exception:
            return {"total_links": 0, "with_content": 0, "latest_collection": None}
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all sources"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            stats = {}
            total_all_links = 0
            total_all_content = 0
            
            for source, source_data in all_data.items():
                total_links = len(source_data)
                with_content = sum(1 for item in source_data if item.get('content_file'))
                latest = max(source_data, key=lambda x: x['collected_at'])['collected_at'] if source_data else None
                
                stats[source] = {
                    "total_links": total_links,
                    "with_content": with_content,
                    "latest_collection": latest
                }
                
                total_all_links += total_links
                total_all_content += with_content
            
            stats["_summary"] = {
                "total_sources": len(all_data),
                "total_links": total_all_links,
                "total_content": total_all_content
            }
            
            return stats
        except Exception:
            return {"_summary": {"total_sources": 0, "total_links": 0, "total_content": 0}}
    
    def get_content_by_timestamp(self, source: str, timestamp: str) -> Optional[str]:
        """Retrieve content by timestamp from source-specific folder"""
        content_file = self.content_dir / source / f"{timestamp}.txt"
        if content_file.exists():
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
        return None
    
    def search_links(self, source: str = None, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> List[Dict]:
        """Search links by date range, optionally filter by source"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            # Collect data from specified source or all sources
            if source:
                data = all_data.get(source, [])
            else:
                data = []
                for source_data in all_data.values():
                    data.extend(source_data)
            
            # Apply date filters
            filtered_data = data
            if start_date:
                filtered_data = [item for item in filtered_data if item['post_date'] >= start_date]
            if end_date:
                filtered_data = [item for item in filtered_data if item['post_date'] <= end_date]
            
            return filtered_data
        except Exception:
            return []
    
    def get_all_sources(self) -> List[str]:
        """Get list of all available sources"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            return list(all_data.keys())
        except Exception:
            return []
    
    def export_source_data(self, source: str, output_file: str):
        """Export data for a specific source to a separate JSON file"""
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            source_data = all_data.get(source, [])
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(source_data, f, indent=2, ensure_ascii=False)
            
            return len(source_data)
        except Exception:
            return 0