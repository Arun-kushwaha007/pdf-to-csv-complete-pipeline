"""
Files API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.schemas import FileResponse, ProcessingJobResponse
from services.file_service import FileService
from services.document_processor import DocumentProcessor
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=ProcessingJobResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    collection_id: str = Form(...),
    group_size: int = Form(25),
    output_format: str = Form("csv"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process multiple PDF files"""
    try:
        # Validate inputs
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if group_size < 1 or group_size > 100:
            raise HTTPException(status_code=400, detail="Group size must be between 1 and 100")
        
        if output_format not in ["csv", "excel", "both"]:
            raise HTTPException(status_code=400, detail="Output format must be csv, excel, or both")
        
        # Validate file types
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        # Create processing job
        service = FileService(db)
        job = service.create_processing_job(
            collection_id=collection_id,
            total_files=len(files),
            group_size=group_size,
            output_format=output_format
        )
        
        # Start background processing
        background_tasks.add_task(
            process_files_background,
            job.id,
            files,
            group_size,
            output_format
        )
        
        return ProcessingJobResponse(
            id=job.id,
            collection_id=job.collection_id,
            status=job.status,
            total_files=job.total_files,
            processed_files=job.processed_files,
            created_at=job.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload files")

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get processing job status"""
    try:
        service = FileService(db)
        job = service.get_processing_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        return ProcessingJobResponse(
            id=job.id,
            collection_id=job.collection_id,
            status=job.status,
            total_files=job.total_files,
            processed_files=job.processed_files,
            total_records=job.total_records,
            duplicates_found=job.duplicates_found,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing job")

@router.get("/jobs", response_model=List[ProcessingJobResponse])
async def get_processing_jobs(
    collection_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get processing jobs with optional filtering"""
    try:
        service = FileService(db)
        jobs = service.get_processing_jobs(
            collection_id=collection_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            ProcessingJobResponse(
                id=job.id,
                collection_id=job.collection_id,
                status=job.status,
                total_files=job.total_files,
                processed_files=job.processed_files,
                total_records=job.total_records,
                duplicates_found=job.duplicates_found,
                error_message=job.error_message,
                created_at=job.created_at,
                completed_at=job.completed_at
            )
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error getting processing jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing jobs")

@router.delete("/jobs/{job_id}")
async def cancel_processing_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a processing job"""
    try:
        service = FileService(db)
        success = service.cancel_processing_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Processing job not found")
        return {"message": "Processing job cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling processing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel processing job")

async def process_files_background(
    job_id: str,
    files: List[UploadFile],
    group_size: int,
    output_format: str
):
    """Background task for processing files"""
    try:
        logger.info(f"Starting background processing for job {job_id}")
        
        # Import here to avoid circular imports
        from models.database import get_db
        from services.document_processor import DocumentProcessor
        from services.duplicate_detector import DuplicateDetector
        from utils.storage import StorageManager
        from utils.config import get_settings
        
        db = next(get_db())
        settings = get_settings()
        
        # Initialize services
        document_processor = DocumentProcessor(settings)
        duplicate_detector = DuplicateDetector()
        storage_manager = StorageManager(settings)
        
        # Update job status
        db.execute(
            "UPDATE processing_jobs SET status = 'processing' WHERE id = %s",
            (job_id,)
        )
        db.commit()
        
        # Process files in groups
        all_records = []
        processed_files = 0
        
        for i in range(0, len(files), group_size):
            group_files = files[i:i + group_size]
            
            # Process group
            group_records = await process_file_group(group_files, job_id, document_processor, storage_manager)
            all_records.extend(group_records)
            
            processed_files += len(group_files)
            
            # Update progress
            db.execute(
                "UPDATE processing_jobs SET processed_files = %s WHERE id = %s",
                (processed_files, job_id)
            )
            db.commit()
        
        # Detect duplicates
        duplicate_count = 0
        if all_records:
            duplicate_count = duplicate_detector.detect_duplicates(all_records)
            
            # Update job with results
            db.execute(
                "UPDATE processing_jobs SET status = 'completed', total_records = %s, duplicates_found = %s, completed_at = %s WHERE id = %s",
                (len(all_records), duplicate_count, datetime.now(), job_id)
            )
            db.commit()
        
        logger.info(f"Background processing completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Background processing error for job {job_id}: {e}")
        
        # Update job status to failed
        db = next(get_db())
        db.execute(
            "UPDATE processing_jobs SET status = 'failed', error_message = %s WHERE id = %s",
            (str(e), job_id)
        )
        db.commit()

async def process_file_group(
    files: List[UploadFile], 
    job_id: str, 
    document_processor: DocumentProcessor,
    storage_manager: StorageManager
) -> List[dict]:
    """Process a group of files"""
    records = []
    
    for file in files:
        try:
            # Save uploaded file
            file_path = await storage_manager.save_uploaded_file(file)
            
            # Process with Document AI
            file_records = await document_processor.process_file(file_path, job_id)
            
            # Add source file info
            for record in file_records:
                record['source_file'] = file.filename
                record['job_id'] = job_id
            
            records.extend(file_records)
            
            # Clean up temp file
            import os
            os.remove(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            continue
    
    return records
