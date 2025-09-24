"""
Database module for IntelliRadar
MongoDB integration for replacing file-based storage
"""

from .mongodb_manager import MongoDBStorageManager, StorageManager
from .mongodb_schema import MongoDBSchema, Collections, DocumentStatus, AnalysisSteps

__all__ = [
    'MongoDBStorageManager',
    'StorageManager',  # Compatibility alias
    'MongoDBSchema', 
    'Collections',
    'DocumentStatus',
    'AnalysisSteps'
]
