"""
File service for managing file uploads and processing jobs
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from models.database import ProcessingJob, Collection
from datetime import datetime

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_processing_job(self, collection_id: str, total_files: int, group_size: int = 25, output_format: str = "csv") -> ProcessingJob:
        """Create a new processing job"""
        try:
            job = ProcessingJob(
                collection_id=collection_id,
                total_files=total_files,
                group_size=group_size,
                output_format=output_format,
                status="pending"
            )
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
            
        except Exception as e:
            logger.error(f"Error creating processing job: {e}")
            self.db.rollback()
            raise
    
    def get_processing_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get processing job by ID"""
        try:
            return self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        except Exception as e:
            logger.error(f"Error getting processing job {job_id}: {e}")
            return None
    
    def get_processing_jobs(self, collection_id: Optional[str] = None, status: Optional[str] = None, 
                           limit: int = 50, offset: int = 0) -> List[ProcessingJob]:
        """Get processing jobs with optional filtering"""
        try:
            query = self.db.query(ProcessingJob)
            
            if collection_id:
                query = query.filter(ProcessingJob.collection_id == collection_id)
            if status:
                query = query.filter(ProcessingJob.status == status)
            
            return query.order_by(ProcessingJob.created_at.desc()).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting processing jobs: {e}")
            return []
    
    def update_processing_job(self, job_id: str, **kwargs) -> bool:
        """Update processing job"""
        try:
            job = self.get_processing_job(job_id)
            if not job:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating processing job {job_id}: {e}")
            self.db.rollback()
            return False
    
    def cancel_processing_job(self, job_id: str) -> bool:
        """Cancel a processing job"""
        try:
            job = self.get_processing_job(job_id)
            if not job:
                return False
            
            if job.status in ["pending", "processing"]:
                job.status = "cancelled"
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling processing job {job_id}: {e}")
            self.db.rollback()
            return False
    
    def delete_processing_job(self, job_id: str) -> bool:
        """Delete a processing job"""
        try:
            job = self.get_processing_job(job_id)
            if not job:
                return False
            
            self.db.delete(job)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting processing job {job_id}: {e}")
            self.db.rollback()
            return False
