#!/usr/bin/env python3
"""
Validate repository structure and connections
"""

import os
from pathlib import Path

def validate_structure():
    """Validate the repository structure"""
    print("Validating repository structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "config.env",
        "deploy_fastapi.py",
        "deploy.sh",
        "setup.sh",
        "README.md",
        "README_DEPLOYMENT.md",
        ".dockerignore",
        ".gitignore"
    ]
    
    required_dirs = [
        "api",
        "models", 
        "services",
        "utils",
        "frontend",
        "frontend/src",
        "frontend/src/components",
        "frontend/src/contexts",
        "frontend/src/pages",
        "frontend/src/services",
        "frontend/public"
    ]
    
    missing_files = []
    missing_dirs = []
    
    # Check files
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    # Check directories
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    # Report results
    if missing_files:
        print(f"Missing files: {missing_files}")
    else:
        print("All required files present")
    
    if missing_dirs:
        print(f"Missing directories: {missing_dirs}")
    else:
        print("All required directories present")
    
    return len(missing_files) == 0 and len(missing_dirs) == 0

def validate_imports():
    """Validate import structure"""
    print("\nValidating import structure...")
    
    # Check main.py imports
    try:
        with open("main.py", "r") as f:
            content = f.read()
            if "from api import" in content:
                print("main.py: API imports OK")
            else:
                print("main.py: Missing API imports")
                return False
            
            if "from models.database import" in content:
                print("main.py: Database imports OK")
            else:
                print("main.py: Missing database imports")
                return False
            
            if "from services." in content:
                print("main.py: Services imports OK")
            else:
                print("main.py: Missing services imports")
                return False
            
            if "from utils." in content:
                print("main.py: Utils imports OK")
            else:
                print("main.py: Missing utils imports")
                return False
                
    except Exception as e:
        print(f"Error reading main.py: {e}")
        return False
    
    return True

def validate_frontend():
    """Validate frontend structure"""
    print("\nValidating frontend structure...")
    
    required_frontend_files = [
        "frontend/package.json",
        "frontend/src/App.js",
        "frontend/src/index.js",
        "frontend/src/index.css",
        "frontend/public/index.html",
        "frontend/public/manifest.json"
    ]
    
    missing_frontend = []
    for file in required_frontend_files:
        if not Path(file).exists():
            missing_frontend.append(file)
    
    if missing_frontend:
        print(f"Missing frontend files: {missing_frontend}")
        return False
    else:
        print("All frontend files present")
        return True

def main():
    """Run validation"""
    print("PDF to CSV Pipeline - Structure Validation")
    print("=" * 50)
    
    structure_ok = validate_structure()
    imports_ok = validate_imports()
    frontend_ok = validate_frontend()
    
    print(f"\nValidation Results:")
    print(f"Structure: {'PASS' if structure_ok else 'FAIL'}")
    print(f"Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"Frontend: {'PASS' if frontend_ok else 'FAIL'}")
    
    if structure_ok and imports_ok and frontend_ok:
        print("\nAll validations passed! Repository is ready for deployment.")
        return 0
    else:
        print("\nSome validations failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())
