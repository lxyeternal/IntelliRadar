"""
MongoDB Storage Manager for IntelliRadar
Replaces the file-based StorageManager with MongoDB operations
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import threading
import sys

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.time_utils import generate_timestamp, get_current_collected_at, get_date_only
from .mongodb_schema import MongoDBSchema, Collections, DocumentStatus, AnalysisSteps


class MongoDBStorageManager:
    """MongoDB-based storage manager replacing file-based StorageManager"""
    
    def __init__(self, connection_string: str = None):
        """Initialize MongoDB storage manager"""
        
        # Initialize MongoDB connection and schema
        self.schema = MongoDBSchema(connection_string)
        self.db = self.schema.db
        
        # Collections shortcuts
        self.links = self.db[Collections.LINKS]
        self.content = self.db[Collections.CONTENT]
        self.analysis = self.db[Collections.ANALYSIS]
        
        # Thread lock for safe operations
        self._lock = threading.Lock()
        
        # Compatibility attributes for legacy crawler code
        self.links_file = "MongoDB Collection: links"
        self.content_dir = Path("MongoDB Collection: content")  
        self.json_dir = Path("MongoDB Collection: analysis")
        
        print(f"✅ MongoDB Storage Manager initialized: {self.db.name}")
    
    def load_existing_links(self, source: str) -> Set[str]:
        """Load existing URLs for a source to avoid duplicates"""
        try:
            # Query all URLs for the specific source
            cursor = self.links.find(
                {"source": source}, 
                {"url": 1, "_id": 0}
            )
            
            urls = set(doc["url"] for doc in cursor)
            print(f"📊 Loaded {len(urls)} existing URLs for source: {source}")
            return urls
            
        except Exception as e:
            print(f"❌ Error loading existing links for {source}: {e}")
            return set()
    
    def save_link_entry(self, source: str, url: str, post_date: str, 
                       timestamp: Optional[str] = None, content: Optional[str] = None) -> str:
        """Save a single link entry and optionally its content"""
        
        if timestamp is None:
            timestamp = generate_timestamp()
        
        # Normalize post_date
        normalized_post_date = get_date_only(post_date)
        if normalized_post_date is None:
            normalized_post_date = post_date
        
        with self._lock:
            try:
                # Prepare link document (simplified schema)
                link_doc = {
                    "timestamp": timestamp,
                    "source": source,
                    "url": url,
                    "post_date": normalized_post_date,
                    "discovered_at": get_current_collected_at(),
                    "status": DocumentStatus.PROCESSED if content else DocumentStatus.PENDING,
                    "has_content": bool(content),
                    "has_analysis": False,
                }
                
                # Insert link document
                result = self.links.insert_one(link_doc)
                
                # Save content if provided
                if content:
                    self.save_content(source, timestamp, content, url, normalized_post_date)
                    
                # Remove source statistics update (no longer needed)
                
                print(f"✅ Link saved: {source} -> {url} [{timestamp}]")
                return timestamp
                
            except DuplicateKeyError:
                print(f"⚠️  Duplicate URL detected: {url}")
                return timestamp
            except Exception as e:
                print(f"❌ Error saving link entry: {e}")
                raise
    
    def save_content(self, source: str, timestamp: str, content: str, url: str = "", post_date: str = ""):
        """Save content to MongoDB content collection (simplified schema)"""
        try:
            content_doc = {
                "timestamp": timestamp,
                "source": source,
                "url": url,
                "content": content,
                "post_date": post_date,
                "collected_at": get_current_collected_at(),
            }
            
            # Insert content documenshi
            self.content.insert_one(content_doc)
            
            # Update link document to reflect content availability
            self.links.update_one(
                {"timestamp": timestamp},
                {
                    "$set": {
                        "has_content": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            word_count = len(content.split()) if content else 0
            print(f"✅ Content saved: {timestamp} ({word_count} words)")
            
        except Exception as e:
            print(f"❌ Error saving content: {e}")
            raise
    
    def save_analysis_results(self, source: str, timestamp: str, analysis_result: dict, url: str = "", post_date: str = ""):
        """Save LLM analysis results to MongoDB analysis collection (simplified schema)"""
        try:
            # Save each analysis step as separate document
            steps_mapping = {
                'step1_output': AnalysisSteps.EXTRACT,
                'step2_output': AnalysisSteps.RELATION, 
                'step3_output': AnalysisSteps.VERIFY,
                # Support both old and new naming conventions
                'extract_output': AnalysisSteps.EXTRACT,
                'relation_output': AnalysisSteps.RELATION,
                'verify_output': AnalysisSteps.VERIFY
            }
            
            for step_key, step_name in steps_mapping.items():
                if analysis_result.get(step_key):
                    step_result = analysis_result[step_key]
                    
                    # Parse JSON string if needed
                    if isinstance(step_result, str):
                        try:
                            step_result = json.loads(step_result)
                        except json.JSONDecodeError:
                            pass  # Keep as string if parsing fails
                    
                    analysis_doc = {
                        "timestamp": timestamp,
                        "source": source,
                        "url": url,
                        "post_date": post_date,
                        "step": step_name,
                        "result": step_result,
                        "created_at": datetime.utcnow(),
                    }
                    
                    self.analysis.insert_one(analysis_doc)
                    print(f"✅ Analysis saved: {timestamp} -> {step_name}")
            
            # Save error if any
            if analysis_result.get('error'):
                error_doc = {
                    "timestamp": timestamp,
                    "source": source,
                    "step": "error",
                    "step_number": 0,
                    "result": {"error": analysis_result['error']},
                    "status": DocumentStatus.FAILED,
                    "error_message": str(analysis_result['error']),
                    "created_at": datetime.utcnow()
                }
                self.analysis.insert_one(error_doc)
            
            # Update link document to reflect analysis availability
            self.links.update_one(
                {"timestamp": timestamp},
                {
                    "$set": {
                        "has_analysis": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            print(f"❌ Error saving analysis results: {e}")
            raise
    
    def save_link_with_data(self, source: str, url: str, post_date: str, 
                           content: str = "", analysis_result: dict = None, 
                           structured_data: dict = None, timestamp: str = None) -> str:
        """
        Universal method to save link entry with optional content, analysis results, or structured data
        
        Args:
            source: Data source name (qianxin, github, snykdb, etc.)
            url: Link URL
            post_date: Publication date
            content: Extracted content (optional)
            analysis_result: LLM analysis results (optional)
            structured_data: Pre-structured data for direct sources (optional)
        """
        # Use provided timestamp or generate new one
        if timestamp is None:
            timestamp = generate_timestamp()
        
        # Automatically determine has_content and has_analysis
        has_content = bool(content and content.strip())
        has_analysis = bool(analysis_result or structured_data)
        
        # Create unified link document
        link_doc = {
            "timestamp": timestamp,
            "source": source,
            "url": url,
            "post_date": get_date_only(post_date) or post_date,
            "collected_at": get_current_collected_at(),
            "status": DocumentStatus.PROCESSED if (has_content or has_analysis) else DocumentStatus.PENDING,
            "has_content": has_content,
            "has_analysis": has_analysis,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add structured_data if provided (for GitHub/SnykDB)
        if structured_data:
            link_doc["structured_data"] = structured_data
        
        # Save link document
        self.links.insert_one(link_doc)
        
        # Save content if provided
        if has_content:
            content_doc = {
                "timestamp": timestamp,
                "source": source,
                "url": url,
                "content": content,
                "extracted_at": datetime.utcnow()
            }
            self.content.insert_one(content_doc)
        
        # Save analysis results if provided
        if analysis_result:
            self.save_analysis_results(source, timestamp, analysis_result, url, post_date)
        elif structured_data:
            # For structured data sources, save as verify step
            verify_doc = {
                "timestamp": timestamp,
                "source": source,
                "url": url,
                "step": AnalysisSteps.VERIFY,
                "step_number": 3,
                "result": structured_data,
                "analyzed_at": datetime.utcnow()
            }
            self.analysis.insert_one(verify_doc)
        
        return timestamp
    
    def save_github_link_with_verify_data(self, url: str, post_date: str, structured_data: dict) -> str:
        """Save GitHub link entry with structured verify data using unified timestamp"""
        timestamp = generate_timestamp()
        
        # Save link entry with unified timestamp (GitHub has no content, but will have analysis)
        self.save_link_entry("github", url, post_date, timestamp)
        
        # Save GitHub structured data as analysis result
        self.save_github_analysis_result(url, timestamp, structured_data)
        
        # Update link to mark that it has analysis data
        self._update_link_analysis_status(url, True)
        
        return timestamp
    
    def save_snyk_vulnerability_data(self, url: str, post_date: str, structured_data: dict) -> str:
        """Save SnykDB vulnerability data with unified timestamp"""
        timestamp = generate_timestamp()
        
        # Save link entry with unified timestamp (SnykDB has no content, but will have analysis)
        self.save_link_entry("snykdb", url, post_date, timestamp)
        
        # Save SnykDB structured data as analysis result
        self.save_snyk_analysis_result(url, timestamp, structured_data)
        
        # Update link to mark that it has analysis data
        self._update_link_analysis_status(url, True)
        
        return timestamp
    
    def save_snyk_analysis_result(self, url: str, timestamp: str, structured_data: dict):
        """Save SnykDB structured data as analysis result in MongoDB"""
        try:
            # Prepare analysis document using standard format
            analysis_doc = {
                "timestamp": timestamp,
                "source": "snykdb", 
                "url": url,
                "post_date": structured_data.get("post_date", ""),
                "step": "verify",
                "result": {
                    "Package Name": structured_data.get("package_name"),
                    "Package Manager": structured_data.get("package_manager"),
                    "Package Version": structured_data.get("package_versions"),
                    "Fix Method": structured_data.get("fix_method"),
                    "Attack Vector": structured_data.get("overview"),
                    "Attack Method": structured_data.get("behavior"),
                    "Update Date": structured_data.get("update_date"),
                    "References": structured_data.get("references"),
                },
                "created_at": datetime.utcnow()
            }
            
            # Insert into analysis collection
            self.analysis.insert_one(analysis_doc)
            
        except Exception as e:
            print(f"Error saving SnykDB analysis result for {url}: {e}")
    
    def get_existing_osv_ids(self) -> Set[str]:
        """Get all existing OSV IDs from database to avoid duplicates"""
        try:
            # Query all OSV entries and extract IDs from the result field
            cursor = self.analysis.find(
                {"source": "osv", "step": "information_verification"},
                {"result.OSV ID": 1, "_id": 0}
            )
            
            ids = set()
            for doc in cursor:
                osv_id = doc.get("result", {}).get("OSV ID", "")
                if osv_id:
                    ids.add(osv_id)
            
            print(f"📊 Loaded {len(ids)} existing OSV IDs from database")
            return ids
            
        except Exception as e:
            print(f"❌ Error loading existing OSV IDs: {e}")
            return set()
    
    def save_osv_vulnerability_data(self, osv_data: dict) -> str:
        """Save OSV vulnerability data directly (no URL, data from local git repo)"""
        timestamp = generate_timestamp()
        
        try:
            # Prepare analysis document for OSV data
            analysis_doc = {
                "timestamp": timestamp,
                "source": "osv",
                "url": "",  # OSV doesn't have URL since it's from local git repo
                "post_date": osv_data.get("published", ""),
                "step": "information_verification",
                "result": {
                    "OSV ID": osv_data.get("id", ""),
                    "Aliases": osv_data.get("aliases", []),
                    "Attack Method": osv_data.get("summary", ""),
                    "Package Manager": osv_data.get("package_manager", ""),
                    "Package Name": osv_data.get("package_name", ""),
                    "Package Version": osv_data.get("package_versions", []),
                    "References": osv_data.get("references", []),
                    "Credits": osv_data.get("credits", [])
                },
                "created_at": datetime.utcnow()
            }
            
            # Insert into analysis collection
            self.analysis.insert_one(analysis_doc)
            
            print(f"✅ Saved OSV data: {osv_data.get('id', 'unknown')} (timestamp: {timestamp})")
            return timestamp
            
        except Exception as e:
            print(f"❌ Error saving OSV data: {e}")
            raise
    
    def _update_link_analysis_status(self, url: str, has_analysis: bool):
        """Update the has_analysis status for a link and set status to completed if it has analysis"""
        try:
            update_fields = {"has_analysis": has_analysis}
            
            # If it has analysis data, set status to processed
            # This is especially important for sources like GitHub, SnykDB, OSV 
            # that don't have content but only have verify/analysis data
            if has_analysis:
                update_fields["status"] = DocumentStatus.PROCESSED
            
            self.links.update_one(
                {"url": url},
                {"$set": update_fields}
            )
        except Exception as e:
            self.logger.error(f"Error updating analysis status for {url}: {e}")
    
    def save_github_analysis_result(self, url: str, timestamp: str, structured_data: dict):
        """Save GitHub structured data as analysis result in MongoDB"""
        try:
            # Prepare analysis document using standard format
            analysis_doc = {
                "timestamp": timestamp,
                "source": "github", 
                "url": url,
                "post_date": structured_data.get("datetime", ""),
                "step": "verify",
                "result": {
                    "Package Name": structured_data.get("package_name"),
                    "Package Manager": structured_data.get("package_manager"),
                    "Package Version": structured_data.get("versions"),
                    "Attack Method": structured_data.get("description"),
                    "GHSA_ID": structured_data.get("ghsa_id")
                },
                "created_at": datetime.utcnow(),
            }
            
            # Insert into analysis collection
            self.analysis.insert_one(analysis_doc)
            print(f"✅ Saved GitHub analysis: {url} (timestamp: {timestamp})")
            
        except Exception as e:
            print(f"❌ Error saving GitHub analysis: {e}")
            raise
    
    def save_link_with_analysis(self, source: str, url: str, post_date: str, 
                               content: str, analysis_result: dict) -> str:
        """Save link entry with content and LLM analysis results (compatibility method)"""
        return self.save_link_with_data(
            source=source,
            url=url, 
            post_date=post_date,
            content=content,
            analysis_result=analysis_result
        )
    
    # Removed get_source_stats method (no longer needed)
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all sources"""
        try:
            # Aggregate statistics from all sources
            pipeline = [
                {
                    "$group": {
                        "_id": "$source",
                        "total_links": {"$sum": 1},
                        "with_content": {"$sum": {"$cond": ["$has_content", 1, 0]}},
                        "with_analysis": {"$sum": {"$cond": ["$has_analysis", 1, 0]}},
                        "latest_collection": {"$max": "$collected_at"}
                    }
                }
            ]
            
            results = list(self.links.aggregate(pipeline))
            
            stats = {}
            total_all_links = 0
            total_all_content = 0
            
            for result in results:
                source = result["_id"]
                total_links = result["total_links"]
                with_content = result["with_content"]
                
                stats[source] = {
                    "total_links": total_links,
                    "with_content": with_content,
                    "with_analysis": result["with_analysis"],
                    "latest_collection": result["latest_collection"]
                }
                
                total_all_links += total_links
                total_all_content += with_content
            
            stats["_summary"] = {
                "total_sources": len(results),
                "total_links": total_all_links,
                "total_content": total_all_content
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting all stats: {e}")
            return {"_summary": {"total_sources": 0, "total_links": 0, "total_content": 0}}
    
    def get_content_by_timestamp(self, source: str, timestamp: str) -> Optional[str]:
        """Retrieve content by timestamp"""
        try:
            content_doc = self.content.find_one({
                "timestamp": timestamp,
                "source": source
            })
            
            return content_doc["content"] if content_doc else None
            
        except Exception as e:
            print(f"❌ Error retrieving content: {e}")
            return None
    
    def search_links(self, source: str = None, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> List[Dict]:
        """Search links by date range, optionally filter by source"""
        try:
            # Build query
            query = {}
            if source:
                query["source"] = source
            if start_date:
                query.setdefault("post_date", {})["$gte"] = start_date
            if end_date:
                query.setdefault("post_date", {})["$lte"] = end_date
            
            # Execute query
            cursor = self.links.find(query).sort("post_date", DESCENDING)
            
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Error searching links: {e}")
            return []
    
    def get_all_sources(self) -> List[str]:
        """Get list of all available sources"""
        try:
            sources = self.links.distinct("source")
            return sorted(sources)
        except Exception as e:
            print(f"❌ Error getting sources: {e}")
            return []
    
    def is_duplicate(self, url: str) -> bool:
        """Check if URL already exists in any source"""
        try:
            return self.links.count_documents({"url": url}) > 0
        except Exception as e:
            print(f"❌ Error checking duplicate: {e}")
            return False
    
    # Removed _update_source_stats method (no longer needed)
            
        except Exception as e:
            print(f"❌ Error updating source stats: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        if hasattr(self, 'schema'):
            self.schema.close()
            print("🔌 MongoDB connection closed")


# Compatibility alias for easy migration
StorageManager = MongoDBStorageManager