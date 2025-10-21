"""
Database models and connection
"""

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database configuration
# Check if running in Cloud Run (has DB_SOCKET_PATH)
DB_SOCKET_PATH = os.getenv("DB_SOCKET_PATH")
if DB_SOCKET_PATH:
    # Use Unix socket for Cloud Run
    DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER', 'pdf2csv_user')}:{os.getenv('DB_PASSWORD', '')}@/{os.getenv('DB_NAME', 'pdf2csv_db')}?host={DB_SOCKET_PATH}"
else:
    # Use TCP for local development
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'pdf2csv_user')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'pdf2csv_db')}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

# Database Models
class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")  # active, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    group_size = Column(Integer, default=25)
    output_format = Column(String(50), default="csv")
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Record(Base):
    __tablename__ = "records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False)
    source_file = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    mobile = Column(String(20))
    landline = Column(String(20))
    address = Column(Text)
    email = Column(String(255))
    date_of_birth = Column(String(50))
    last_seen_date = Column(String(50))
    is_duplicate = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    is_reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False)
    mobile_number = Column(String(20), nullable=False)
    record_count = Column(Integer, default=1)
    is_resolved = Column(Boolean, default=False)
    resolution_action = Column(String(50))  # keep_first, keep_most_complete, manual_merge, ignore
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExportJob(Base):
    __tablename__ = "export_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id"))
    export_type = Column(String(50), nullable=False)  # csv, excel, zip
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    file_path = Column(String(500))
    file_size = Column(Integer, default=0)
    record_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.id"))
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
async def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Database utilities
def execute_raw_query(query: str, params: tuple = None):
    """Execute raw SQL query"""
    db = SessionLocal()
    try:
        result = db.execute(query, params or ())
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        db.close()

def get_raw_query_results(query: str, params: tuple = None):
    """Get results from raw SQL query"""
    db = SessionLocal()
    try:
        result = db.execute(query, params or ())
        return result.fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        db.close()
