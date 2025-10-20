"""
Configuration management
"""

import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Google Cloud Configuration
    PROJECT_ID: str = "pdf2csv-475708"
    LOCATION: str = "us"
    CUSTOM_PROCESSOR_ID: str = "9585689d6bfa6148"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Database Configuration
    DB_HOST: str = "34.58.120.64"
    DB_PORT: int = 5432
    DB_NAME: str = "pdf2csv_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "@Sharing1234"
    DB_SSL: bool = True
    DB_SOCKET_PATH: Optional[str] = "/cloudsql/pdf2csv-475708:us-central1:pdf2csv-db"
    
    # Storage Configuration
    UPLOAD_DIR: str = "uploads"
    EXPORT_DIR: str = "exports"
    TEMP_DIR: str = "temp"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [".pdf"]
    
    # Processing Configuration
    DEFAULT_GROUP_SIZE: int = 25
    MAX_GROUP_SIZE: int = 100
    MAX_CONCURRENT_JOBS: int = 5
    
    # Export Configuration
    DEFAULT_EXPORT_FORMAT: str = "csv"
    DEFAULT_ENCODING: str = "utf-8"
    DEFAULT_DELIMITER: str = ","
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = "config.env"
        case_sensitive = True

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
