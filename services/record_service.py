"""
Record service for managing records
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.database import Record, ProcessingJob, DuplicateGroup
from models.schemas import RecordUpdate
from datetime import datetime

logger = logging.getLogger(__name__)

class RecordService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_records(self, job_id: Optional[str] = None, collection_id: Optional[str] = None,
                   include_duplicates: bool = True, is_valid: Optional[bool] = None,
                   search: Optional[str] = None, limit: int = 1000, offset: int = 0) -> List[Record]:
        """Get records with optional filtering"""
        try:
            query = self.db.query(Record)
            
            if job_id:
                query = query.filter(Record.job_id == job_id)
            
            if collection_id:
                query = query.join(ProcessingJob).filter(ProcessingJob.collection_id == collection_id)
            
            if not include_duplicates:
                query = query.filter(Record.is_duplicate == False)
            
            if is_valid is not None:
                query = query.filter(Record.is_valid == is_valid)
            
            if search:
                search_filter = or_(
                    Record.first_name.ilike(f"%{search}%"),
                    Record.last_name.ilike(f"%{search}%"),
                    Record.mobile.ilike(f"%{search}%"),
                    Record.address.ilike(f"%{search}%"),
                    Record.email.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            return query.order_by(Record.created_at.desc()).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting records: {e}")
            return []
    
    def get_record_by_id(self, record_id: str) -> Optional[Record]:
        """Get record by ID"""
        try:
            return self.db.query(Record).filter(Record.id == record_id).first()
        except Exception as e:
            logger.error(f"Error getting record {record_id}: {e}")
            return None
    
    def update_record(self, record_id: str, record_data: RecordUpdate) -> Optional[Record]:
        """Update a record"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return None
            
            # Update fields
            if record_data.first_name is not None:
                record.first_name = record_data.first_name
            if record_data.last_name is not None:
                record.last_name = record_data.last_name
            if record_data.mobile is not None:
                record.mobile = record_data.mobile
            if record_data.landline is not None:
                record.landline = record_data.landline
            if record_data.address is not None:
                record.address = record_data.address
            if record_data.email is not None:
                record.email = record_data.email
            if record_data.date_of_birth is not None:
                record.date_of_birth = record_data.date_of_birth
            if record_data.last_seen_date is not None:
                record.last_seen_date = record_data.last_seen_date
            if record_data.is_valid is not None:
                record.is_valid = record_data.is_valid
            if record_data.is_reviewed is not None:
                record.is_reviewed = record_data.is_reviewed
            if record_data.reviewer_notes is not None:
                record.reviewer_notes = record_data.reviewer_notes
            
            record.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            self.db.rollback()
            raise
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a record"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return False
            
            self.db.delete(record)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            self.db.rollback()
            return False
    
    def validate_record(self, record_id: str, is_valid: bool) -> bool:
        """Mark a record as valid or invalid"""
        try:
            record = self.get_record_by_id(record_id)
            if not record:
                return False
            
            record.is_valid = is_valid
            record.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating record {record_id}: {e}")
            self.db.rollback()
            return False
    
    def get_duplicate_groups(self, job_id: Optional[str] = None, collection_id: Optional[str] = None,
                           limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get duplicate groups"""
        try:
            query = self.db.query(DuplicateGroup)
            
            if job_id:
                query = query.filter(DuplicateGroup.job_id == job_id)
            
            if collection_id:
                query = query.join(ProcessingJob).filter(ProcessingJob.collection_id == collection_id)
            
            groups = query.order_by(DuplicateGroup.record_count.desc()).offset(offset).limit(limit).all()
            
            # Get records for each group
            result = []
            for group in groups:
                records = self.db.query(Record).filter(
                    and_(
                        Record.job_id == group.job_id,
                        Record.mobile == group.mobile_number,
                        Record.is_duplicate == True
                    )
                ).all()
                
                result.append({
                    'id': group.id,
                    'job_id': group.job_id,
                    'mobile_number': group.mobile_number,
                    'record_count': group.record_count,
                    'is_resolved': group.is_resolved,
                    'resolution_action': group.resolution_action,
                    'records': records,
                    'created_at': group.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting duplicate groups: {e}")
            return []
    
    def resolve_duplicates(self, duplicate_group_id: str, keep_record_id: str) -> bool:
        """Resolve duplicates by keeping one record and removing others"""
        try:
            group = self.db.query(DuplicateGroup).filter(DuplicateGroup.id == duplicate_group_id).first()
            if not group:
                return False
            
            # Get all records in the duplicate group
            records = self.db.query(Record).filter(
                and_(
                    Record.job_id == group.job_id,
                    Record.mobile == group.mobile_number,
                    Record.is_duplicate == True
                )
            ).all()
            
            # Mark the keep record as not duplicate
            keep_record = self.db.query(Record).filter(Record.id == keep_record_id).first()
            if keep_record:
                keep_record.is_duplicate = False
                keep_record.updated_at = datetime.utcnow()
            
            # Mark group as resolved
            group.is_resolved = True
            group.resolution_action = "manual_merge"
            group.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving duplicates: {e}")
            self.db.rollback()
            return False
    
    def bulk_validate_records(self, record_ids: List[str], is_valid: bool) -> int:
        """Bulk validate records"""
        try:
            updated_count = 0
            
            for record_id in record_ids:
                if self.validate_record(record_id, is_valid):
                    updated_count += 1
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error bulk validating records: {e}")
            return 0
    
    def bulk_delete_records(self, record_ids: List[str]) -> int:
        """Bulk delete records"""
        try:
            deleted_count = 0
            
            for record_id in record_ids:
                if self.delete_record(record_id):
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error bulk deleting records: {e}")
            return 0
    
    def get_records_summary(self, job_id: Optional[str] = None, collection_id: Optional[str] = None) -> Dict[str, int]:
        """Get records summary statistics"""
        try:
            query = self.db.query(Record)
            
            if job_id:
                query = query.filter(Record.job_id == job_id)
            
            if collection_id:
                query = query.join(ProcessingJob).filter(ProcessingJob.collection_id == collection_id)
            
            records = query.all()
            
            total_records = len(records)
            valid_records = len([r for r in records if r.is_valid])
            invalid_records = total_records - valid_records
            duplicate_records = len([r for r in records if r.is_duplicate])
            reviewed_records = len([r for r in records if r.is_reviewed])
            unreviewed_records = total_records - reviewed_records
            
            return {
                'total_records': total_records,
                'valid_records': valid_records,
                'invalid_records': invalid_records,
                'duplicate_records': duplicate_records,
                'reviewed_records': reviewed_records,
                'unreviewed_records': unreviewed_records
            }
            
        except Exception as e:
            logger.error(f"Error getting records summary: {e}")
            return {}
