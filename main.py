"""
FastAPI Backend for PDF to CSV Pipeline
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from typing import List, Optional
import asyncio
from datetime import datetime
import uuid

# Import our modules
from api import collections, files, records, exports
from models.database import init_db, get_db
from services.document_processor import DocumentProcessor
from services.duplicate_detector import DuplicateDetector
from services.export_service import ExportService
from utils.storage import StorageManager
from utils.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
document_processor = None
duplicate_detector = None
export_service = None
storage_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global document_processor, duplicate_detector, export_service, storage_manager
    
    # Startup
    logger.info("Starting PDF to CSV Pipeline API...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize services
        settings = get_settings()
        document_processor = DocumentProcessor(settings)
        duplicate_detector = DuplicateDetector()
        export_service = ExportService()
        storage_manager = StorageManager(settings)
        
        logger.info("Services initialized")
        
        # Create necessary directories
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("exports", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down PDF to CSV Pipeline API...")

# Create FastAPI app
app = FastAPI(
    title="PDF to CSV Pipeline API",
    description="AI-powered PDF processing and contact extraction",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for React app
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Include API routers
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(records.router, prefix="/api/records", tags=["records"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])

@app.get("/")
async def serve_react_app():
    """Serve React app"""
    return FileResponse("frontend/build/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/stats")
async def get_stats():
    """Get application statistics"""
    try:
        db = next(get_db())
        
        # Get basic stats
        collections_count = db.execute("SELECT COUNT(*) FROM collections").scalar()
        records_count = db.execute("SELECT COUNT(*) FROM records").scalar()
        processing_jobs_count = db.execute("SELECT COUNT(*) FROM processing_jobs WHERE status = 'processing'").scalar()
        
        return {
            "collections": collections_count,
            "records": records_count,
            "processing_jobs": processing_jobs_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.post("/api/process-pdfs")
async def process_pdfs(
    background_tasks: BackgroundTasks,
    collection_id: str = Form(...),
    group_size: int = Form(25),
    output_format: str = Form("csv"),
    files: List[UploadFile] = File(...)
):
    """Process multiple PDF files"""
    try:
        # Validate inputs
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if group_size < 1 or group_size > 100:
            raise HTTPException(status_code=400, detail="Group size must be between 1 and 100")
        
        # Create processing job
        job_id = str(uuid.uuid4())
        
        # Start background processing
        background_tasks.add_task(
            process_pdfs_background,
            job_id,
            collection_id,
            files,
            group_size,
            output_format
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Processing {len(files)} files in background"
        }
        
    except Exception as e:
        logger.error(f"Error processing PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_pdfs_background(
    job_id: str,
    collection_id: str,
    files: List[UploadFile],
    group_size: int,
    output_format: str
):
    """Background task for processing PDFs"""
    try:
        logger.info(f"Starting background processing for job {job_id}")
        
        # Update job status
        db = next(get_db())
        db.execute(
            "UPDATE processing_jobs SET status = 'processing', total_files = %s WHERE id = %s",
            (len(files), job_id)
        )
        db.commit()
        
        # Process files in groups
        all_records = []
        processed_files = 0
        
        for i in range(0, len(files), group_size):
            group_files = files[i:i + group_size]
            
            # Process group
            group_records = await process_file_group(group_files, job_id)
            all_records.extend(group_records)
            
            processed_files += len(group_files)
            
            # Update progress
            db.execute(
                "UPDATE processing_jobs SET processed_files = %s WHERE id = %s",
                (processed_files, job_id)
            )
            db.commit()
        
        # Detect duplicates
        if all_records:
            duplicate_count = duplicate_detector.detect_duplicates(all_records)
            
            # Update job with results
            db.execute(
                "UPDATE processing_jobs SET status = 'completed', total_records = %s, duplicates_found = %s WHERE id = %s",
                (len(all_records), duplicate_count, job_id)
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

async def process_file_group(files: List[UploadFile], job_id: str) -> List[dict]:
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
            os.remove(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            continue
    
    return records

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
