"""
File storage management
"""

import os
import shutil
import tempfile
import logging
from typing import Optional
from fastapi import UploadFile
from utils.config import get_settings

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.settings.UPLOAD_DIR,
            self.settings.EXPORT_DIR,
            self.settings.TEMP_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file to temporary location"""
        try:
            # Validate file
            if not self._is_valid_file(file):
                raise ValueError(f"Invalid file: {file.filename}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(file.filename)[1],
                dir=self.settings.TEMP_DIR
            )
            
            # Write file content
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            
            logger.info(f"Saved uploaded file: {file.filename} -> {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error saving uploaded file {file.filename}: {e}")
            raise
    
    def _is_valid_file(self, file: UploadFile) -> bool:
        """Validate uploaded file"""
        try:
            # Check file extension
            if not file.filename:
                return False
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in self.settings.ALLOWED_EXTENSIONS:
                return False
            
            # Check file size (if available)
            if hasattr(file, 'size') and file.size:
                if file.size > self.settings.MAX_FILE_SIZE:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False
    
    def save_file(self, content: bytes, filename: str, directory: str = None) -> str:
        """Save file content to specified directory"""
        try:
            target_dir = directory or self.settings.UPLOAD_DIR
            os.makedirs(target_dir, exist_ok=True)
            
            file_path = os.path.join(target_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved file: {filename} -> {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise
    
    def get_file_path(self, filename: str, directory: str = None) -> Optional[str]:
        """Get file path if it exists"""
        try:
            target_dir = directory or self.settings.UPLOAD_DIR
            file_path = os.path.join(target_dir, filename)
            
            if os.path.exists(file_path):
                return file_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file path {filename}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file if it exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified age"""
        try:
            import time
            
            cleaned_count = 0
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.settings.TEMP_DIR):
                file_path = os.path.join(self.settings.TEMP_DIR, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except Exception as e:
            logger.error(f"Error getting file size {file_path}: {e}")
            return 0
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info {file_path}: {e}")
            return None
    
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy file from source to destination"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied file: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file {source_path} to {dest_path}: {e}")
            return False
    
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move file from source to destination"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(source_path, dest_path)
            logger.info(f"Moved file: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {source_path} to {dest_path}: {e}")
            return False
