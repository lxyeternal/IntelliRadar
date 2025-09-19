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
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.time_utils import generate_timestamp, get_current_collected_at, get_date_only


class StorageManager:
    """Unified storage manager for crawler data"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.links_dir = self.base_dir / "links"
        self.links_file = self.links_dir / "all_links.json"  # 统一的JSON文件
        self.content_dir = self.base_dir / "content"
        self.json_dir = self.base_dir / "json"  # LLM分析结果存储目录
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.links_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread lock for safe JSON file operations
        self._lock = threading.Lock()
        
        # Initialize links file if it doesn't exist
        if not self.links_file.exists():
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
    
    # Timestamp generation is now handled by time_utils.generate_timestamp()
    
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
            timestamp = generate_timestamp()
        
        # Convert post_date to date-only format
        normalized_post_date = get_date_only(post_date)
        if normalized_post_date is None:
            normalized_post_date = post_date  # fallback to original if parsing fails
        
        # Prepare link entry
        entry = {
            "timestamp": timestamp,
            "source": source,
            "post_date": normalized_post_date,
            "url": url,
            "collected_at": get_current_collected_at(),
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
    
    def is_duplicate(self, url: str) -> bool:
        """Check if URL already exists in any source"""
        with self._lock:
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
                
                # Check all sources for this URL
                for source_data in all_data.values():
                    for item in source_data:
                        if item['url'] == url:
                            return True
                return False
            except Exception:
                return False
    
    def save_analysis_results(self, source: str, timestamp: str, analysis_result: dict):
        """Save LLM analysis results to JSON files in source-specific directory"""
        try:
            # Create source-specific json directory
            source_json_dir = self.json_dir / source
            source_json_dir.mkdir(exist_ok=True)
            
            # Save step 1 (extraction) results
            if analysis_result.get('step1_output'):
                extract_file = source_json_dir / f"{timestamp}_extract.json"
                with open(extract_file, 'w', encoding='utf-8') as f:
                    # Parse JSON string if it's a string, otherwise use as-is
                    step1_result = analysis_result['step1_output']
                    if isinstance(step1_result, str):
                        try:
                            step1_result = json.loads(step1_result)
                        except json.JSONDecodeError:
                            # If parsing fails, keep as string
                            pass
                    
                    json.dump({
                        'timestamp': timestamp,
                        'step': 'entity_extraction',
                        'result': step1_result,
                        'threat_indicators': analysis_result.get('threat_indicators', [])
                    }, f, ensure_ascii=False, indent=2)
            
            # Save step 2 (relation) results  
            if analysis_result.get('step2_output'):
                relation_file = source_json_dir / f"{timestamp}_relation.json"
                with open(relation_file, 'w', encoding='utf-8') as f:
                    # Parse JSON string if it's a string, otherwise use as-is
                    step2_result = analysis_result['step2_output']
                    if isinstance(step2_result, str):
                        try:
                            step2_result = json.loads(step2_result)
                        except json.JSONDecodeError:
                            # If parsing fails, keep as string
                            pass
                    
                    json.dump({
                        'timestamp': timestamp,
                        'step': 'relation_analysis',
                        'result': step2_result
                    }, f, ensure_ascii=False, indent=2)
            
            # Save step 3 (verify) results
            if analysis_result.get('step3_output'):
                verify_file = source_json_dir / f"{timestamp}_verify.json"
                with open(verify_file, 'w', encoding='utf-8') as f:
                    # Parse JSON string if it's a string, otherwise use as-is
                    step3_result = analysis_result['step3_output']
                    if isinstance(step3_result, str):
                        try:
                            step3_result = json.loads(step3_result)
                        except json.JSONDecodeError:
                            # If parsing fails, keep as string
                            pass
                    
                    json.dump({
                        'timestamp': timestamp,
                        'step': 'information_verification',
                        'result': step3_result
                    }, f, ensure_ascii=False, indent=2)
            
            # Save error information if any
            if analysis_result.get('error'):
                error_file = source_json_dir / f"{timestamp}_error.json"
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'error': analysis_result['error']
                    }, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            # Note: Can't use self.logger here as StorageManager doesn't have logger
            print(f"Failed to save analysis results for {timestamp}: {e}")
    
    def save_link_with_analysis(self, source: str, url: str, post_date: str, 
                               content: str, analysis_result: dict) -> str:
        """Save link entry with content and LLM analysis results"""
        timestamp = generate_timestamp()
        
        # Save link entry with content
        self.save_link_entry(source, url, post_date, timestamp, content)
        
        # Save analysis results
        self.save_analysis_results(source, timestamp, analysis_result)
        
        return timestamp