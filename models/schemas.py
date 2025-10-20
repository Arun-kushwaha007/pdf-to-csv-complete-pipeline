"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

# Collection schemas
class CollectionCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    client_name: str = Field(..., min_length=1, max_length=255, description="Client name")
    description: Optional[str] = Field(None, description="Collection description")

class CollectionUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(active|archived)$")

class CollectionResponse(BaseSchema):
    id: UUID
    name: str
    client_name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

# Processing Job schemas
class ProcessingJobResponse(BaseSchema):
    id: UUID
    collection_id: UUID
    status: str
    total_files: int
    processed_files: int
    total_records: Optional[int] = None
    duplicates_found: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Record schemas
class RecordCreate(BaseSchema):
    job_id: UUID
    source_file: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    landline: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    last_seen_date: Optional[str] = None
    confidence_score: Optional[float] = None

class RecordUpdate(BaseSchema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    landline: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    last_seen_date: Optional[str] = None
    is_valid: Optional[bool] = None
    is_reviewed: Optional[bool] = None
    reviewer_notes: Optional[str] = None

class RecordResponse(BaseSchema):
    id: UUID
    job_id: UUID
    source_file: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    mobile: Optional[str]
    landline: Optional[str]
    address: Optional[str]
    email: Optional[str]
    date_of_birth: Optional[str]
    last_seen_date: Optional[str]
    is_duplicate: bool
    is_valid: bool
    is_reviewed: bool
    reviewer_notes: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime

# Duplicate Group schemas
class DuplicateGroupResponse(BaseSchema):
    id: UUID
    job_id: UUID
    mobile_number: str
    record_count: int
    is_resolved: bool
    resolution_action: Optional[str]
    records: List[RecordResponse]
    created_at: datetime

# Export schemas
class ExportRequest(BaseSchema):
    record_ids: Optional[List[UUID]] = None
    job_id: Optional[UUID] = None
    collection_id: Optional[UUID] = None
    export_type: str = Field(..., regex="^(csv|excel|zip)$")
    include_duplicates: bool = False
    include_invalid: bool = False
    group_by: Optional[str] = Field(None, regex="^(collection|job|none)$")
    encoding: str = Field("utf-8", regex="^(utf-8|latin-1)$")
    delimiter: str = Field(",", regex="^[,;\\t]$")
    
    @validator('record_ids', 'job_id', 'collection_id')
    def validate_at_least_one(cls, v, values):
        if not v and not values.get('job_id') and not values.get('collection_id'):
            raise ValueError('Must specify at least one of: record_ids, job_id, or collection_id')
        return v

class ExportResponse(BaseSchema):
    id: UUID
    status: str
    export_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    record_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ExportHistoryResponse(BaseSchema):
    id: UUID
    export_type: str
    status: str
    file_size: Optional[int]
    record_count: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

# File upload schemas
class FileUploadResponse(BaseSchema):
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime

# Statistics schemas
class CollectionStatsResponse(BaseSchema):
    total_collections: int
    active_collections: int
    archived_collections: int
    total_records: int
    total_processing_jobs: int
    active_processing_jobs: int

class RecordsSummaryResponse(BaseSchema):
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    reviewed_records: int
    unreviewed_records: int

# Error schemas
class ErrorResponse(BaseSchema):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Success schemas
class SuccessResponse(BaseSchema):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Search and filter schemas
class SearchRequest(BaseSchema):
    query: str = Field(..., min_length=1, max_length=255)
    fields: Optional[List[str]] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class FilterRequest(BaseSchema):
    field: str = Field(..., min_length=1)
    operator: str = Field(..., regex="^(eq|ne|gt|gte|lt|lte|like|in|not_in)$")
    value: Any
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)

# Bulk operation schemas
class BulkOperationRequest(BaseSchema):
    record_ids: List[UUID] = Field(..., min_items=1)
    operation: str = Field(..., regex="^(validate|invalidate|delete|review|unreview)$")
    value: Optional[Any] = None

class BulkOperationResponse(BaseSchema):
    operation: str
    affected_count: int
    message: str
