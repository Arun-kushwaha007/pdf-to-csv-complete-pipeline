"""
Records API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.schemas import RecordResponse, RecordUpdate, DuplicateGroupResponse
from services.record_service import RecordService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[RecordResponse])
async def get_records(
    job_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    include_duplicates: bool = True,
    is_valid: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get records with optional filtering"""
    try:
        service = RecordService(db)
        records = service.get_records(
            job_id=job_id,
            collection_id=collection_id,
            include_duplicates=include_duplicates,
            is_valid=is_valid,
            search=search,
            limit=limit,
            offset=offset
        )
        return records
    except Exception as e:
        logger.error(f"Error getting records: {e}")
        raise HTTPException(status_code=500, detail="Failed to get records")

@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific record by ID"""
    try:
        service = RecordService(db)
        record = service.get_record_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get record")

@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(
    record_id: str,
    record: RecordUpdate,
    db: Session = Depends(get_db)
):
    """Update a record"""
    try:
        service = RecordService(db)
        updated_record = service.update_record(record_id, record)
        if not updated_record:
            raise HTTPException(status_code=404, detail="Record not found")
        return updated_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update record")

@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Delete a record"""
    try:
        service = RecordService(db)
        success = service.delete_record(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"message": "Record deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete record")

@router.post("/{record_id}/validate")
async def validate_record(
    record_id: str,
    is_valid: bool,
    db: Session = Depends(get_db)
):
    """Mark a record as valid or invalid"""
    try:
        service = RecordService(db)
        success = service.validate_record(record_id, is_valid)
        if not success:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"message": f"Record marked as {'valid' if is_valid else 'invalid'}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate record")

@router.get("/duplicates/groups", response_model=List[DuplicateGroupResponse])
async def get_duplicate_groups(
    job_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get duplicate groups"""
    try:
        service = RecordService(db)
        groups = service.get_duplicate_groups(
            job_id=job_id,
            collection_id=collection_id,
            limit=limit,
            offset=offset
        )
        return groups
    except Exception as e:
        logger.error(f"Error getting duplicate groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to get duplicate groups")

@router.post("/duplicates/resolve")
async def resolve_duplicates(
    duplicate_group_id: str,
    keep_record_id: str,
    db: Session = Depends(get_db)
):
    """Resolve duplicates by keeping one record and removing others"""
    try:
        service = RecordService(db)
        success = service.resolve_duplicates(duplicate_group_id, keep_record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Duplicate group not found")
        return {"message": "Duplicates resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving duplicates: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve duplicates")

@router.post("/bulk/validate")
async def bulk_validate_records(
    record_ids: List[str],
    is_valid: bool,
    db: Session = Depends(get_db)
):
    """Bulk validate records"""
    try:
        service = RecordService(db)
        updated_count = service.bulk_validate_records(record_ids, is_valid)
        return {"message": f"{updated_count} records updated"}
    except Exception as e:
        logger.error(f"Error bulk validating records: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk validate records")

@router.delete("/bulk/delete")
async def bulk_delete_records(
    record_ids: List[str],
    db: Session = Depends(get_db)
):
    """Bulk delete records"""
    try:
        service = RecordService(db)
        deleted_count = service.bulk_delete_records(record_ids)
        return {"message": f"{deleted_count} records deleted"}
    except Exception as e:
        logger.error(f"Error bulk deleting records: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete records")

@router.get("/stats/summary")
async def get_records_summary(
    job_id: Optional[str] = None,
    collection_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get records summary statistics"""
    try:
        service = RecordService(db)
        summary = service.get_records_summary(job_id=job_id, collection_id=collection_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting records summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get records summary")
