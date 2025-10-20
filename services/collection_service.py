"""
Collection service for managing collections
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from models.database import Collection, ProcessingJob, Record
from models.schemas import CollectionCreate, CollectionUpdate
from datetime import datetime

logger = logging.getLogger(__name__)

class CollectionService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_collections(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Collection]:
        """Get collections with optional filtering"""
        try:
            query = self.db.query(Collection)
            
            if status:
                query = query.filter(Collection.status == status)
            
            return query.order_by(Collection.created_at.desc()).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []
    
    def get_collection_by_id(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID"""
        try:
            return self.db.query(Collection).filter(Collection.id == collection_id).first()
        except Exception as e:
            logger.error(f"Error getting collection {collection_id}: {e}")
            return None
    
    def create_collection(self, collection_data: CollectionCreate) -> Collection:
        """Create a new collection"""
        try:
            collection = Collection(
                name=collection_data.name,
                client_name=collection_data.client_name,
                description=collection_data.description
            )
            
            self.db.add(collection)
            self.db.commit()
            self.db.refresh(collection)
            
            return collection
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            self.db.rollback()
            raise
    
    def update_collection(self, collection_id: str, collection_data: CollectionUpdate) -> Optional[Collection]:
        """Update a collection"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if not collection:
                return None
            
            # Update fields
            if collection_data.name is not None:
                collection.name = collection_data.name
            if collection_data.client_name is not None:
                collection.client_name = collection_data.client_name
            if collection_data.description is not None:
                collection.description = collection_data.description
            if collection_data.status is not None:
                collection.status = collection_data.status
            
            collection.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(collection)
            
            return collection
            
        except Exception as e:
            logger.error(f"Error updating collection {collection_id}: {e}")
            self.db.rollback()
            raise
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if not collection:
                return False
            
            self.db.delete(collection)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_id}: {e}")
            self.db.rollback()
            return False
    
    def archive_collection(self, collection_id: str) -> bool:
        """Archive a collection"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if not collection:
                return False
            
            collection.status = "archived"
            collection.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error archiving collection {collection_id}: {e}")
            self.db.rollback()
            return False
    
    def unarchive_collection(self, collection_id: str) -> bool:
        """Unarchive a collection"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if not collection:
                return False
            
            collection.status = "active"
            collection.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error unarchiving collection {collection_id}: {e}")
            self.db.rollback()
            return False
    
    def get_collection_stats(self, collection_id: str) -> Optional[dict]:
        """Get statistics for a collection"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if not collection:
                return None
            
            # Get processing jobs for this collection
            jobs = self.db.query(ProcessingJob).filter(ProcessingJob.collection_id == collection_id).all()
            
            # Calculate statistics
            total_jobs = len(jobs)
            completed_jobs = len([job for job in jobs if job.status == "completed"])
            processing_jobs = len([job for job in jobs if job.status == "processing"])
            failed_jobs = len([job for job in jobs if job.status == "failed"])
            
            # Get total records
            total_records = 0
            total_duplicates = 0
            
            for job in jobs:
                if job.total_records:
                    total_records += job.total_records
                if job.duplicates_found:
                    total_duplicates += job.duplicates_found
            
            return {
                "collection_id": collection_id,
                "collection_name": collection.name,
                "client_name": collection.client_name,
                "status": collection.status,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "processing_jobs": processing_jobs,
                "failed_jobs": failed_jobs,
                "total_records": total_records,
                "total_duplicates": total_duplicates,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats {collection_id}: {e}")
            return None
