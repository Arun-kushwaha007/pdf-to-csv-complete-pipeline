"""
Exports API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.schemas import ExportRequest, ExportResponse, ExportHistoryResponse
from services.export_service import ExportService
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=ExportResponse)
async def generate_export(
    background_tasks: BackgroundTasks,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Generate export for records"""
    try:
        service = ExportService(db)
        
        # Validate export request
        if not export_request.record_ids and not export_request.job_id and not export_request.collection_id:
            raise HTTPException(status_code=400, detail="Must specify record_ids, job_id, or collection_id")
        
        # Create export job
        export_job = service.create_export_job(export_request)
        
        # Start background export generation
        background_tasks.add_task(
            generate_export_background,
            export_job.id,
            export_request
        )
        
        return ExportResponse(
            id=export_job.id,
            status=export_job.status,
            export_type=export_job.export_type,
            created_at=export_job.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating export: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate export")

@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: str,
    db: Session = Depends(get_db)
):
    """Get export status and details"""
    try:
        service = ExportService(db)
        export_job = service.get_export_job(export_id)
        if not export_job:
            raise HTTPException(status_code=404, detail="Export not found")
        
        return ExportResponse(
            id=export_job.id,
            status=export_job.status,
            export_type=export_job.export_type,
            file_path=export_job.file_path,
            file_size=export_job.file_size,
            record_count=export_job.record_count,
            error_message=export_job.error_message,
            created_at=export_job.created_at,
            completed_at=export_job.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export {export_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export")

@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    db: Session = Depends(get_db)
):
    """Download export file"""
    try:
        service = ExportService(db)
        export_job = service.get_export_job(export_id)
        if not export_job:
            raise HTTPException(status_code=404, detail="Export not found")
        
        if export_job.status != "completed":
            raise HTTPException(status_code=400, detail="Export not ready for download")
        
        if not export_job.file_path or not os.path.exists(export_job.file_path):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        # Determine media type based on file extension
        file_extension = os.path.splitext(export_job.file_path)[1].lower()
        media_types = {
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.zip': 'application/zip'
        }
        media_type = media_types.get(file_extension, 'application/octet-stream')
        
        # Generate filename
        filename = f"export_{export_id}{file_extension}"
        
        return FileResponse(
            path=export_job.file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export {export_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download export")

@router.get("/history/list", response_model=List[ExportHistoryResponse])
async def get_export_history(
    collection_id: Optional[str] = None,
    export_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get export history"""
    try:
        service = ExportService(db)
        exports = service.get_export_history(
            collection_id=collection_id,
            export_type=export_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            ExportHistoryResponse(
                id=export.id,
                export_type=export.export_type,
                status=export.status,
                file_size=export.file_size,
                record_count=export.record_count,
                created_at=export.created_at,
                completed_at=export.completed_at
            )
            for export in exports
        ]
    except Exception as e:
        logger.error(f"Error getting export history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export history")

@router.delete("/{export_id}")
async def delete_export(
    export_id: str,
    db: Session = Depends(get_db)
):
    """Delete export and its file"""
    try:
        service = ExportService(db)
        success = service.delete_export(export_id)
        if not success:
            raise HTTPException(status_code=404, detail="Export not found")
        return {"message": "Export deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete export")

@router.post("/bulk/delete")
async def bulk_delete_exports(
    export_ids: List[str],
    db: Session = Depends(get_db)
):
    """Bulk delete exports"""
    try:
        service = ExportService(db)
        deleted_count = service.bulk_delete_exports(export_ids)
        return {"message": f"{deleted_count} exports deleted"}
    except Exception as e:
        logger.error(f"Error bulk deleting exports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete exports")

async def generate_export_background(
    export_id: str,
    export_request: ExportRequest
):
    """Background task for generating export"""
    try:
        logger.info(f"Starting background export generation for {export_id}")
        
        # Import here to avoid circular imports
        from models.database import get_db
        from services.export_service import ExportService
        
        db = next(get_db())
        service = ExportService(db)
        
        # Update status to processing
        db.execute(
            "UPDATE export_jobs SET status = 'processing' WHERE id = %s",
            (export_id,)
        )
        db.commit()
        
        # Generate export
        file_path = await service.generate_export_file(export_id, export_request)
        
        # Update status to completed
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        db.execute(
            "UPDATE export_jobs SET status = 'completed', file_path = %s, file_size = %s, completed_at = %s WHERE id = %s",
            (file_path, file_size, datetime.now(), export_id)
        )
        db.commit()
        
        logger.info(f"Background export generation completed for {export_id}")
        
    except Exception as e:
        logger.error(f"Background export generation error for {export_id}: {e}")
        
        # Update status to failed
        db = next(get_db())
        db.execute(
            "UPDATE export_jobs SET status = 'failed', error_message = %s WHERE id = %s",
            (str(e), export_id)
        )
        db.commit()
