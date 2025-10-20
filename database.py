"""
Database connection and operations for PDF to CSV Pipeline
Uses Google Cloud SQL with PostgreSQL
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_pool = None
        self._initialize_connection_pool()
    
    def _initialize_connection_pool(self):
        """Initialize connection pool to Cloud SQL"""
        try:
            # Cloud SQL connection parameters
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'pdf2csv_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'sslmode': 'require' if os.getenv('DB_SSL', 'true').lower() == 'true' else 'disable'
            }
            
            # For Cloud SQL, use Unix socket if available
            if os.getenv('DB_SOCKET_PATH'):
                db_config['host'] = os.getenv('DB_SOCKET_PATH')
                db_config.pop('port', None)
            
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_config
            )
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Optional[List[Dict]]:
        """Execute a database query"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                conn.commit()
                return None
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute multiple queries with different parameters"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
    
    # Collection operations
    def create_collection(self, collection_name: str, client_name: str, notes: str = None, batch_id: str = None) -> str:
        """Create a new collection"""
        query = """
        INSERT INTO collections (collection_name, client_name, notes, batch_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (collection_name, client_name, notes, batch_id), fetch=True)
        return str(result[0]['id'])
    
    def get_collections(self, status: str = None, client_name: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get collections with optional filtering"""
        query = """
        SELECT id, collection_name, client_name, created_date, last_updated_date, 
               status, notes, batch_id, total_records
        FROM collections
        WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if client_name:
            query += " AND client_name ILIKE %s"
            params.append(f"%{client_name}%")
        
        query += " ORDER BY created_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    def get_collection_by_id(self, collection_id: str) -> Optional[Dict]:
        """Get a specific collection by ID"""
        query = """
        SELECT id, collection_name, client_name, created_date, last_updated_date,
               status, notes, batch_id, total_records
        FROM collections WHERE id = %s
        """
        result = self.execute_query(query, (collection_id,), fetch=True)
        return result[0] if result else None
    
    def update_collection(self, collection_id: str, **kwargs) -> bool:
        """Update collection fields"""
        allowed_fields = ['collection_name', 'client_name', 'status', 'notes', 'batch_id']
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                params.append(value)
        
        if not updates:
            return False
        
        params.append(collection_id)
        query = f"UPDATE collections SET {', '.join(updates)} WHERE id = %s"
        
        self.execute_query(query, tuple(params))
        return True
    
    def archive_collection(self, collection_id: str) -> bool:
        """Archive a collection"""
        return self.update_collection(collection_id, status='archived')
    
    def unarchive_collection(self, collection_id: str) -> bool:
        """Unarchive a collection"""
        return self.update_collection(collection_id, status='active')
    
    # Batch operations
    def create_batch(self, collection_id: str, batch_name: str, group_size: int = 25) -> str:
        """Create a new batch"""
        query = """
        INSERT INTO batches (collection_id, batch_name, group_size)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (collection_id, batch_name, group_size), fetch=True)
        return str(result[0]['id'])
    
    def get_batches_by_collection(self, collection_id: str) -> List[Dict]:
        """Get all batches for a collection"""
        query = """
        SELECT id, batch_name, group_size, status, total_files, processed_files,
               total_records, filtered_records, duplicates_found,
               processing_started_at, processing_completed_at, created_at
        FROM batches WHERE collection_id = %s
        ORDER BY created_at DESC
        """
        return self.execute_query(query, (collection_id,), fetch=True)
    
    def update_batch_status(self, batch_id: str, status: str, **kwargs) -> bool:
        """Update batch status and other fields"""
        allowed_fields = ['total_files', 'processed_files', 'total_records', 'filtered_records', 
                         'duplicates_found', 'processing_started_at', 'processing_completed_at']
        updates = ['status = %s']
        params = [status]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                params.append(value)
        
        params.append(batch_id)
        query = f"UPDATE batches SET {', '.join(updates)} WHERE id = %s"
        
        self.execute_query(query, tuple(params))
        return True
    
    # File operations
    def create_file(self, batch_id: str, file_name: str, file_path: str = None, 
                   file_size: int = None, pages: int = None) -> str:
        """Create a new file record"""
        query = """
        INSERT INTO files (batch_id, file_name, file_path, file_size, pages)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (batch_id, file_name, file_path, file_size, pages), fetch=True)
        return str(result[0]['id'])
    
    def update_file_status(self, file_id: str, status: str, **kwargs) -> bool:
        """Update file status and processing details"""
        allowed_fields = ['document_ai_operation_id', 'raw_json_path', 'processing_time_seconds', 
                         'error_message', 'pages']
        updates = ['status = %s']
        params = [status]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                params.append(value)
        
        params.append(file_id)
        query = f"UPDATE files SET {', '.join(updates)} WHERE id = %s"
        
        self.execute_query(query, tuple(params))
        return True
    
    def get_files_by_batch(self, batch_id: str) -> List[Dict]:
        """Get all files for a batch"""
        query = """
        SELECT id, file_name, file_path, file_size, status, pages,
               document_ai_operation_id, processing_time_seconds, error_message, created_at
        FROM files WHERE batch_id = %s
        ORDER BY created_at ASC
        """
        return self.execute_query(query, (batch_id,), fetch=True)
    
    # Record operations
    def create_records(self, batch_id: str, file_id: str, records: List[Dict]) -> int:
        """Create multiple records for a batch and file"""
        if not records:
            return 0
        
        query = """
        INSERT INTO records (batch_id, file_id, first_name, last_name, mobile, landline,
                           address, email, date_of_birth, last_seen_date, confidence_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params_list = []
        for record in records:
            params_list.append((
                batch_id, file_id,
                record.get('first_name', ''),
                record.get('last_name', ''),
                record.get('mobile', ''),
                record.get('landline', ''),
                record.get('address', ''),
                record.get('email', ''),
                record.get('date_of_birth', ''),
                record.get('last_seen_date', ''),
                record.get('confidence_score', 0.0)
            ))
        
        self.execute_many(query, params_list)
        return len(records)
    
    def get_records_by_batch(self, batch_id: str, include_duplicates: bool = True, 
                           limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Get records for a batch with optional filtering"""
        query = """
        SELECT r.id, r.first_name, r.last_name, r.mobile, r.landline, r.address,
               r.email, r.date_of_birth, r.last_seen_date, r.is_duplicate,
               r.is_valid, r.is_reviewed, r.reviewer_notes, r.confidence_score,
               f.file_name, r.created_at
        FROM records r
        JOIN files f ON r.file_id = f.id
        WHERE r.batch_id = %s
        """
        params = [batch_id]
        
        if not include_duplicates:
            query += " AND r.is_duplicate = FALSE"
        
        query += " ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    def get_duplicate_records(self, batch_id: str) -> List[Dict]:
        """Get duplicate records grouped by mobile number"""
        query = """
        SELECT r.mobile, dg.id as duplicate_group_id, dg.record_count,
               array_agg(
                   json_build_object(
                       'id', r.id,
                       'first_name', r.first_name,
                       'last_name', r.last_name,
                       'mobile', r.mobile,
                       'address', r.address,
                       'email', r.email,
                       'file_name', f.file_name
                   )
               ) as records
        FROM records r
        JOIN files f ON r.file_id = f.id
        JOIN duplicate_groups dg ON r.duplicate_group_id = dg.id
        WHERE r.batch_id = %s AND r.is_duplicate = TRUE
        GROUP BY r.mobile, dg.id, dg.record_count
        ORDER BY dg.record_count DESC
        """
        return self.execute_query(query, (batch_id,), fetch=True)
    
    def mark_record_as_duplicate(self, record_id: str, duplicate_group_id: str) -> bool:
        """Mark a record as duplicate"""
        query = """
        UPDATE records 
        SET is_duplicate = TRUE, duplicate_group_id = %s
        WHERE id = %s
        """
        self.execute_query(query, (duplicate_group_id, record_id))
        return True
    
    def mark_record_as_valid(self, record_id: str, is_valid: bool = True) -> bool:
        """Mark a record as valid or invalid"""
        query = "UPDATE records SET is_valid = %s WHERE id = %s"
        self.execute_query(query, (is_valid, record_id))
        return True
    
    def update_record(self, record_id: str, **kwargs) -> bool:
        """Update record fields"""
        allowed_fields = ['first_name', 'last_name', 'mobile', 'landline', 'address', 
                         'email', 'date_of_birth', 'last_seen_date', 'is_valid', 
                         'is_reviewed', 'reviewer_notes']
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = %s")
                params.append(value)
        
        if not updates:
            return False
        
        params.append(record_id)
        query = f"UPDATE records SET {', '.join(updates)} WHERE id = %s"
        
        self.execute_query(query, tuple(params))
        return True
    
    # Duplicate detection
    def detect_duplicates(self, batch_id: str) -> int:
        """Detect and flag duplicates in a batch"""
        query = "SELECT detect_duplicates_in_batch(%s)"
        result = self.execute_query(query, (batch_id,), fetch=True)
        return result[0]['detect_duplicates_in_batch'] if result else 0
    
    # Export operations
    def create_export_record(self, collection_id: str, batch_id: str, export_type: str, 
                           file_path: str, file_size: int, record_count: int) -> str:
        """Create an export record"""
        query = """
        INSERT INTO export_history (collection_id, batch_id, export_type, file_path, file_size, record_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (collection_id, batch_id, export_type, file_path, file_size, record_count), fetch=True)
        return str(result[0]['id'])
    
    def get_export_history(self, collection_id: str = None, limit: int = 50) -> List[Dict]:
        """Get export history"""
        query = """
        SELECT eh.id, eh.export_type, eh.file_path, eh.file_size, eh.record_count,
               eh.status, eh.created_at, c.collection_name, b.batch_name
        FROM export_history eh
        JOIN collections c ON eh.collection_id = c.id
        JOIN batches b ON eh.batch_id = b.id
        WHERE 1=1
        """
        params = []
        
        if collection_id:
            query += " AND eh.collection_id = %s"
            params.append(collection_id)
        
        query += " ORDER BY eh.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    # Logging operations
    def log_processing_event(self, batch_id: str, file_id: str, log_level: str, 
                           message: str, details: Dict = None) -> None:
        """Log a processing event"""
        query = """
        INSERT INTO processing_logs (batch_id, file_id, log_level, message, details)
        VALUES (%s, %s, %s, %s, %s)
        """
        details_json = json.dumps(details) if details else None
        self.execute_query(query, (batch_id, file_id, log_level, message, details_json))
    
    def get_processing_logs(self, batch_id: str = None, limit: int = 100) -> List[Dict]:
        """Get processing logs"""
        query = """
        SELECT pl.id, pl.log_level, pl.message, pl.details, pl.created_at,
               c.collection_name, b.batch_name, f.file_name
        FROM processing_logs pl
        LEFT JOIN batches b ON pl.batch_id = b.id
        LEFT JOIN collections c ON b.collection_id = c.id
        LEFT JOIN files f ON pl.file_id = f.id
        WHERE 1=1
        """
        params = []
        
        if batch_id:
            query += " AND pl.batch_id = %s"
            params.append(batch_id)
        
        query += " ORDER BY pl.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    def close(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()
