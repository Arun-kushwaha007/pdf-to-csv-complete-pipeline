#!/usr/bin/env python3
"""
Local development startup script for PDF to CSV Pipeline
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Start the FastAPI application locally"""
    print("🚀 Starting PDF to CSV Pipeline locally...")
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Please run from project root.")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("❌ Dependencies not installed. Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Start the application
    print("✅ Starting FastAPI server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
