#!/usr/bin/env python3
"""
Test script to verify all components are properly connected
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("Testing component connections...")
    
    try:
        # Test main application
        print("  Testing main.py imports...")
        from main import app
        print("    FastAPI app imported successfully")
        
        # Test API modules
        print("  Testing API modules...")
        from api import collections, files, records, exports
        print("    All API modules imported successfully")
        
        # Test models
        print("  Testing models...")
        from models.database import init_db, get_db, Collection, ProcessingJob, Record
        from models.schemas import CollectionCreate, CollectionUpdate, CollectionResponse
        print("    All models imported successfully")
        
        # Test services
        print("  Testing services...")
        from services.document_processor import DocumentProcessor
        from services.duplicate_detector import DuplicateDetector
        from services.export_service import ExportService
        from services.collection_service import CollectionService
        from services.file_service import FileService
        from services.record_service import RecordService
        print("    All services imported successfully")
        
        # Test utils
        print("  Testing utilities...")
        from utils.config import get_settings
        from utils.storage import StorageManager
        print("    All utilities imported successfully")
        
        print("\nAll components are properly connected!")
        return True
        
    except ImportError as e:
        print(f"\nImport error: {e}")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from utils.config import get_settings
        settings = get_settings()
        
        print(f"  Project ID: {settings.PROJECT_ID}")
        print(f"  Database: {settings.DB_NAME}")
        print(f"  Document AI Processor: {settings.CUSTOM_PROCESSOR_ID}")
        
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

def test_database_models():
    """Test database model definitions"""
    print("\nTesting database models...")
    
    try:
        from models.database import Collection, ProcessingJob, Record, DuplicateGroup, ExportJob
        
        # Test model creation
        collection = Collection(name="Test", client_name="Test Client")
        print("  Collection model created")
        
        job = ProcessingJob(collection_id=collection.id)
        print("  ProcessingJob model created")
        
        record = Record(job_id=job.id, first_name="Test", last_name="User")
        print("  Record model created")
        
        return True
        
    except Exception as e:
        print(f"Database model error: {e}")
        return False

def main():
    """Run all tests"""
    print("PDF to CSV Pipeline - Component Connection Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All components are properly connected and ready for deployment!")
        return 0
    else:
        print("Some components have issues. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
