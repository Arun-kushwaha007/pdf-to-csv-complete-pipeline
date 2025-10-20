#!/usr/bin/env python3
"""
Test script for database connection and basic operations
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Add current directory to path
sys.path.append('.')

from database import db_manager

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        # Test basic connection
        collections = db_manager.get_collections(limit=1)
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_collection_operations():
    """Test collection CRUD operations"""
    print("\n📁 Testing collection operations...")
    
    try:
        # Create test collection
        collection_id = db_manager.create_collection(
            collection_name="Test Collection",
            client_name="Test Client",
            notes="This is a test collection"
        )
        print(f"✅ Created collection: {collection_id}")
        
        # Get collection
        collection = db_manager.get_collection_by_id(collection_id)
        if collection:
            print(f"✅ Retrieved collection: {collection['collection_name']}")
        else:
            print("❌ Failed to retrieve collection")
            return False
        
        # Update collection
        success = db_manager.update_collection(collection_id, notes="Updated test collection")
        if success:
            print("✅ Updated collection")
        else:
            print("❌ Failed to update collection")
            return False
        
        # Archive collection
        success = db_manager.archive_collection(collection_id)
        if success:
            print("✅ Archived collection")
        else:
            print("❌ Failed to archive collection")
            return False
        
        # Unarchive collection
        success = db_manager.unarchive_collection(collection_id)
        if success:
            print("✅ Unarchived collection")
        else:
            print("❌ Failed to unarchive collection")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Collection operations failed: {e}")
        return False

def test_batch_operations():
    """Test batch operations"""
    print("\n📦 Testing batch operations...")
    
    try:
        # Create test collection first
        collection_id = db_manager.create_collection(
            collection_name="Batch Test Collection",
            client_name="Batch Test Client"
        )
        
        # Create batch
        batch_id = db_manager.create_batch(
            collection_id=collection_id,
            batch_name="Test Batch",
            group_size=25
        )
        print(f"✅ Created batch: {batch_id}")
        
        # Update batch status
        success = db_manager.update_batch_status(
            batch_id, 
            'processing', 
            total_files=5,
            processed_files=2
        )
        if success:
            print("✅ Updated batch status")
        else:
            print("❌ Failed to update batch status")
            return False
        
        # Get batches
        batches = db_manager.get_batches_by_collection(collection_id)
        if batches:
            print(f"✅ Retrieved {len(batches)} batches")
        else:
            print("❌ Failed to retrieve batches")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Batch operations failed: {e}")
        return False

def test_record_operations():
    """Test record operations"""
    print("\n📋 Testing record operations...")
    
    try:
        # Create test collection and batch
        collection_id = db_manager.create_collection(
            collection_name="Record Test Collection",
            client_name="Record Test Client"
        )
        
        batch_id = db_manager.create_batch(
            collection_id=collection_id,
            batch_name="Record Test Batch"
        )
        
        # Create test file
        file_id = db_manager.create_file(
            batch_id=batch_id,
            file_name="test.pdf",
            file_size=1024
        )
        
        # Create test records
        test_records = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'mobile': '0412345678',
                'address': '123 Test Street, Test City',
                'email': 'john.doe@example.com'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'mobile': '0498765432',
                'address': '456 Test Avenue, Test City',
                'email': 'jane.smith@example.com'
            }
        ]
        
        records_created = db_manager.create_records(batch_id, file_id, test_records)
        print(f"✅ Created {records_created} records")
        
        # Get records
        records = db_manager.get_records_by_batch(batch_id)
        if records:
            print(f"✅ Retrieved {len(records)} records")
        else:
            print("❌ Failed to retrieve records")
            return False
        
        # Test duplicate detection
        duplicates_found = db_manager.detect_duplicates(batch_id)
        print(f"✅ Duplicate detection found {duplicates_found} duplicates")
        
        return True
        
    except Exception as e:
        print(f"❌ Record operations failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Database Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Collection Operations", test_collection_operations),
        ("Batch Operations", test_batch_operations),
        ("Record Operations", test_record_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check your database configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
