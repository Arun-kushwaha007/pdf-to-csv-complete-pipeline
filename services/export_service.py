"""
Export service for generating CSV, Excel, and ZIP files
"""

import os
import tempfile
import zipfile
import logging
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import Record, ProcessingJob, Collection
from utils.storage import StorageManager

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.storage_manager = StorageManager()
    
    def create_export_job(self, export_request) -> 'ExportJob':
        """Create a new export job"""
        try:
            from models.database import ExportJob
            
            export_job = ExportJob(
                collection_id=export_request.collection_id,
                job_id=export_request.job_id,
                export_type=export_request.export_type,
                status="pending"
            )
            
            self.db.add(export_job)
            self.db.commit()
            self.db.refresh(export_job)
            
            return export_job
            
        except Exception as e:
            logger.error(f"Error creating export job: {e}")
            self.db.rollback()
            raise
    
    def get_export_job(self, export_id: str) -> Optional['ExportJob']:
        """Get export job by ID"""
        try:
            from models.database import ExportJob
            return self.db.query(ExportJob).filter(ExportJob.id == export_id).first()
        except Exception as e:
            logger.error(f"Error getting export job {export_id}: {e}")
            return None
    
    def get_export_history(self, collection_id: Optional[str] = None, export_type: Optional[str] = None, 
                          status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List['ExportJob']:
        """Get export history with filtering"""
        try:
            from models.database import ExportJob
            
            query = self.db.query(ExportJob)
            
            if collection_id:
                query = query.filter(ExportJob.collection_id == collection_id)
            if export_type:
                query = query.filter(ExportJob.export_type == export_type)
            if status:
                query = query.filter(ExportJob.status == status)
            
            return query.order_by(ExportJob.created_at.desc()).offset(offset).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting export history: {e}")
            return []
    
    async def generate_export_file(self, export_id: str, export_request) -> str:
        """Generate export file"""
        try:
            export_job = self.get_export_job(export_id)
            if not export_job:
                raise ValueError("Export job not found")
            
            # Get records based on request
            records = await self._get_records_for_export(export_request)
            
            if not records:
                raise ValueError("No records found for export")
            
            # Generate file based on type
            if export_request.export_type == "csv":
                file_path = await self._generate_csv(records, export_request)
            elif export_request.export_type == "excel":
                file_path = await self._generate_excel(records, export_request)
            elif export_request.export_type == "zip":
                file_path = await self._generate_zip(records, export_request)
            else:
                raise ValueError(f"Unsupported export type: {export_request.export_type}")
            
            # Update export job with file info
            export_job.file_path = file_path
            export_job.file_size = os.path.getsize(file_path)
            export_job.record_count = len(records)
            
            self.db.commit()
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating export file: {e}")
            raise
    
    async def _get_records_for_export(self, export_request) -> List[Dict]:
        """Get records for export based on request"""
        try:
            query = self.db.query(Record)
            
            # Filter by record IDs
            if export_request.record_ids:
                query = query.filter(Record.id.in_(export_request.record_ids))
            
            # Filter by job ID
            if export_request.job_id:
                query = query.filter(Record.job_id == export_request.job_id)
            
            # Filter by collection ID
            if export_request.collection_id:
                query = query.join(ProcessingJob).filter(ProcessingJob.collection_id == export_request.collection_id)
            
            # Apply filters
            if not export_request.include_duplicates:
                query = query.filter(Record.is_duplicate == False)
            
            if not export_request.include_invalid:
                query = query.filter(Record.is_valid == True)
            
            records = query.all()
            
            # Convert to dictionaries
            return [
                {
                    'id': str(record.id),
                    'first_name': record.first_name,
                    'last_name': record.last_name,
                    'mobile': record.mobile,
                    'landline': record.landline,
                    'address': record.address,
                    'email': record.email,
                    'date_of_birth': record.date_of_birth,
                    'last_seen_date': record.last_seen_date,
                    'source_file': record.source_file,
                    'is_duplicate': record.is_duplicate,
                    'is_valid': record.is_valid,
                    'confidence_score': record.confidence_score
                }
                for record in records
            ]
            
        except Exception as e:
            logger.error(f"Error getting records for export: {e}")
            return []
    
    async def _generate_csv(self, records: List[Dict], export_request) -> str:
        """Generate CSV file"""
        try:
            # Create DataFrame
            df = pd.DataFrame(records)
            
            # Remove internal fields
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            # Create temp file
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            # Save CSV
            df.to_csv(
                file_path,
                index=False,
                encoding=export_request.encoding,
                sep=export_request.delimiter
            )
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            raise
    
    async def _generate_excel(self, records: List[Dict], export_request) -> str:
        """Generate Excel file"""
        try:
            # Create DataFrame
            df = pd.DataFrame(records)
            
            # Remove internal fields
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            # Create temp file
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            # Save Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating Excel: {e}")
            raise
    
    async def _generate_zip(self, records: List[Dict], export_request) -> str:
        """Generate ZIP file with multiple formats"""
        try:
            # Create DataFrame
            df = pd.DataFrame(records)
            
            # Remove internal fields
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Add CSV file
                csv_path = os.path.join(temp_dir, "records.csv")
                df.to_csv(csv_path, index=False, encoding=export_request.encoding, sep=export_request.delimiter)
                zipf.write(csv_path, "records.csv")
                
                # Add Excel file
                excel_path = os.path.join(temp_dir, "records.xlsx")
                df.to_excel(excel_path, index=False, engine='openpyxl')
                zipf.write(excel_path, "records.xlsx")
                
                # Add filtered CSV (remove duplicates)
                filtered_df = df[~df.get('is_duplicate', False)]
                filtered_csv_path = os.path.join(temp_dir, "filtered_records.csv")
                filtered_df.to_csv(filtered_csv_path, index=False, encoding=export_request.encoding, sep=export_request.delimiter)
                zipf.write(filtered_csv_path, "filtered_records.csv")
                
                # Add summary
                summary_data = {
                    'Total Records': len(df),
                    'Filtered Records': len(filtered_df),
                    'Duplicates': len(df[df.get('is_duplicate', False)]),
                    'Export Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Export Type': export_request.export_type
                }
                summary_df = pd.DataFrame([summary_data])
                summary_csv_path = os.path.join(temp_dir, "summary.csv")
                summary_df.to_csv(summary_csv_path, index=False, encoding=export_request.encoding, sep=export_request.delimiter)
                zipf.write(summary_csv_path, "summary.csv")
            
            return zip_path
            
        except Exception as e:
            logger.error(f"Error generating ZIP: {e}")
            raise
    
    def delete_export(self, export_id: str) -> bool:
        """Delete export and its file"""
        try:
            export_job = self.get_export_job(export_id)
            if not export_job:
                return False
            
            # Delete file if it exists
            if export_job.file_path and os.path.exists(export_job.file_path):
                os.remove(export_job.file_path)
            
            # Delete from database
            self.db.delete(export_job)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting export {export_id}: {e}")
            self.db.rollback()
            return False
    
    def bulk_delete_exports(self, export_ids: List[str]) -> int:
        """Bulk delete exports"""
        try:
            deleted_count = 0
            
            for export_id in export_ids:
                if self.delete_export(export_id):
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error bulk deleting exports: {e}")
            return 0
