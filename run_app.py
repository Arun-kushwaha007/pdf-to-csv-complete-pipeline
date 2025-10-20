#!/usr/bin/env python3
"""
Startup script for PDF to CSV Pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    print("🔍 Checking requirements...")
    
    try:
        import streamlit
        import pandas
        import psycopg2
        from database import db_manager
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Check database connection"""
    print("🔍 Checking database connection...")
    
    try:
        from database import db_manager
        collections = db_manager.get_collections(limit=1)
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration in config.env")
        return False

def check_environment():
    """Check environment variables"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'PROJECT_ID',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your config.env file")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def start_application():
    """Start the Streamlit application"""
    print("🚀 Starting PDF to CSV Pipeline...")
    
    try:
        # Run the main application
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app_new.py',
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--server.headless', 'true'
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

def main():
    """Main function"""
    print("📄 PDF to CSV Pipeline - Startup Script")
    print("=" * 50)
    
    # Check if config.env exists
    if not Path('config.env').exists():
        print("❌ config.env file not found")
        print("Please create a config.env file with your configuration")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config.env')
    
    # Run checks
    checks = [
        ("Requirements", check_requirements),
        ("Environment", check_environment),
        ("Database", check_database_connection)
    ]
    
    for check_name, check_func in checks:
        if not check_func():
            print(f"\n❌ {check_name} check failed. Please fix the issues and try again.")
            return False
    
    print("\n✅ All checks passed!")
    print("Starting application...")
    
    # Start the application
    start_application()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
