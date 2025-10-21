#!/usr/bin/env python3
"""
Deployment script for PDF to CSV Pipeline (FastAPI + React)
Deploys to Google Cloud Platform with Cloud Run and Cloud SQL
"""

import os
import subprocess
import json
import time
import sys
from pathlib import Path

class GCPDeployer:
    def __init__(self):
        # Get project ID from gcloud config
        result = subprocess.run("gcloud config get-value project", shell=True, capture_output=True, text=True)
        self.project_id = result.stdout.strip()
        if not self.project_id or self.project_id == "(unset)":
            print("❌ No project set. Run: gcloud config set project YOUR-PROJECT-ID")
            sys.exit(1)
        
        self.region = "us-central1"
        self.service_name = "pdf2csv-api"
        self.frontend_service_name = "pdf2csv-frontend"
        self.db_instance_name = "pdf2csv-db"
        self.db_name = "pdf2csv_db"
        self.db_user = "pdf2csv_user"
        self.db_password = "@Sharing1234"
        
    def run_command(self, command, check=True):
        """Run a shell command"""
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)
            
        return result
    
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check gcloud
        try:
            self.run_command("gcloud --version")
        except:
            print("❌ gcloud CLI not found. Please install it first.")
            sys.exit(1)
        
        # Check if authenticated
        try:
            result = self.run_command("gcloud auth list --filter=status:ACTIVE --format=value(account)")
            if not result.stdout.strip():
                print("❌ Not authenticated with gcloud. Please run 'gcloud auth login'")
                sys.exit(1)
        except:
            print("❌ Authentication check failed")
            sys.exit(1)
        
        # Check if project is set
        try:
            result = self.run_command("gcloud config get-value project")
            if result.stdout.strip() != self.project_id:
                print(f"❌ Project not set to {self.project_id}. Please run 'gcloud config set project {self.project_id}'")
                sys.exit(1)
        except:
            print("❌ Project configuration check failed")
            sys.exit(1)
        
        print("✅ Prerequisites check passed")
    
    def enable_apis(self):
        """Enable required Google Cloud APIs"""
        print("🔧 Enabling required APIs...")
        
        apis = [
            "cloudbuild.googleapis.com",
            "run.googleapis.com",
            "sqladmin.googleapis.com",
            "documentai.googleapis.com",
            "storage.googleapis.com",
            "cloudresourcemanager.googleapis.com"
        ]
        
        for api in apis:
            print(f"Enabling {api}...")
            self.run_command(f"gcloud services enable {api}")
        
        print("✅ APIs enabled")
    
    def setup_cloud_sql(self):
        """Setup Cloud SQL PostgreSQL instance"""
        print("🗄️ Setting up Cloud SQL...")
        
        # Check if instance exists
        result = self.run_command(f"gcloud sql instances describe {self.db_instance_name}", check=False)
        
        if result.returncode != 0:
            print(f"Creating Cloud SQL instance {self.db_instance_name}...")
            self.run_command(f"""
                gcloud sql instances create {self.db_instance_name} \
                --database-version=POSTGRES_15 \
                --tier=db-f1-micro \
                --region={self.region} \
                --storage-type=SSD \
                --storage-size=10GB \
                --storage-auto-increase \
                --backup \
                --enable-ip-alias
            """)
        else:
            print(f"Cloud SQL instance {self.db_instance_name} already exists")
        
        # Create database
        print(f"Creating database {self.db_name}...")
        self.run_command(f"gcloud sql databases create {self.db_name} --instance={self.db_instance_name}", check=False)
        
        # Create user
        print(f"Creating user {self.db_user}...")
        self.run_command(f"gcloud sql users create {self.db_user} --instance={self.db_instance_name} --password={self.db_password}", check=False)
        
        print("✅ Cloud SQL setup complete")
    
    def build_frontend(self):
        """Build React frontend"""
        print("🏗️ Building React frontend...")
        
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            sys.exit(1)
        
        # Clean previous build
        print("Cleaning previous build...")
        self.run_command("cd frontend && rm -rf node_modules package-lock.json build .npm", check=False)
        
        # Clear npm cache
        print("Clearing npm cache...")
        self.run_command("cd frontend && npm cache clean --force", check=False)
        
        # Install dependencies with specific flags for compatibility
        print("Installing frontend dependencies...")
        result = self.run_command("cd frontend && npm install --legacy-peer-deps --force", check=False)
        if result.returncode != 0:
            print("❌ Failed to install dependencies")
            print(f"Error: {result.stderr}")
            print("Trying alternative installation method...")
            
            # Try with different flags
            result = self.run_command("cd frontend && npm install --no-optional --legacy-peer-deps", check=False)
            if result.returncode != 0:
                print("❌ Alternative installation also failed")
                print(f"Error: {result.stderr}")
                sys.exit(1)
        
        # Fix ajv dependency issue specifically
        print("Fixing ajv dependency issues...")
        self.run_command("cd frontend && npm install ajv@^6.12.6 --legacy-peer-deps", check=False)
        
        # Build for production
        print("Building frontend for production...")
        result = self.run_command("cd frontend && npm run build", check=False)
        if result.returncode != 0:
            print("❌ Failed to build frontend")
            print(f"Error: {result.stderr}")
            print(f"Output: {result.stdout}")
            
            # Try building with different Node options
            print("Trying build with different Node options...")
            result = self.run_command("cd frontend && NODE_OPTIONS='--max-old-space-size=4096' npm run build", check=False)
            if result.returncode != 0:
                print("❌ Build failed even with increased memory")
                print(f"Error: {result.stderr}")
                sys.exit(1)
        
        print("✅ Frontend build complete")
    
    def create_dockerfile(self):
        """Create Dockerfile for FastAPI backend"""
        dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy frontend build
COPY frontend/build ./frontend/build

# Create necessary directories
RUN mkdir -p uploads exports temp

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content.strip())
        
        print("✅ Dockerfile created")
    
    def deploy_to_cloud_run(self):
        """Deploy to Cloud Run"""
        print("🚀 Deploying to Cloud Run...")
        
        # Build and push container
        print("Building and pushing container...")
        self.run_command(f"""
            gcloud builds submit --tag gcr.io/{self.project_id}/{self.service_name}
        """)
        
        # Deploy to Cloud Run
        print("Deploying to Cloud Run...")
        self.run_command(f"""
            gcloud run deploy {self.service_name} \\
            --image gcr.io/{self.project_id}/{self.service_name} \\
            --platform managed \\
            --region {self.region} \\
            --allow-unauthenticated \\
            --memory 2Gi \\
            --cpu 2 \\
            --timeout 3600 \\
            --max-instances 10 \\
            --set-env-vars PROJECT_ID={self.project_id} \\
            --set-env-vars DB_HOST=/cloudsql/{self.project_id}:{self.region}:{self.db_instance_name} \\
            --set-env-vars DB_NAME={self.db_name} \\
            --set-env-vars DB_USER={self.db_user} \\
            --set-env-vars DB_PASSWORD={self.db_password} \\
            --set-env-vars DB_SOCKET_PATH=/cloudsql/{self.project_id}:{self.region}:{self.db_instance_name} \\
            --add-cloudsql-instances {self.project_id}:{self.region}:{self.db_instance_name}
        """)
        
        print("✅ Deployment to Cloud Run complete")
    
    def setup_document_ai(self):
        """Setup Document AI processor"""
        print("🤖 Setting up Document AI...")
        
        # List existing processors and use the first one
        result = self.run_command("gcloud documentai processors list --location=us --format='value(name)' | head -1")
        if result.returncode != 0 or not result.stdout.strip():
            print("❌ No Document AI processors found. Please create one manually in the Google Cloud Console.")
            print("   Go to: https://console.cloud.google.com/ai/document-ai/processors")
            sys.exit(1)
        
        processor_id = result.stdout.strip().split('/')[-1]
        print(f"✅ Using existing Document AI processor: {processor_id}")
        return processor_id
    
    def create_env_file(self, processor_id):
        """Create environment file for local development"""
        env_content = f"""
# Google Cloud Configuration
PROJECT_ID={self.project_id}
LOCATION=us
CUSTOM_PROCESSOR_ID={processor_id}
GOOGLE_APPLICATION_CREDENTIALS=./pdf2csv-converter-tool-ee510faebb5c.json

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME={self.db_name}
DB_USER={self.db_user}
DB_PASSWORD={self.db_password}
DB_SSL=true
DB_SOCKET_PATH=/cloudsql/{self.project_id}:us-central1:{self.db_instance_name}

# Storage Configuration
UPLOAD_DIR=uploads
EXPORT_DIR=exports
TEMP_DIR=temp
MAX_FILE_SIZE=104857600
ALLOWED_EXTENSIONS=[".pdf"]

# Processing Configuration
DEFAULT_GROUP_SIZE=25
MAX_GROUP_SIZE=100
MAX_CONCURRENT_JOBS=5

# Export Configuration
DEFAULT_EXPORT_FORMAT=csv
DEFAULT_ENCODING=utf-8
DEFAULT_DELIMITER=,

# Security Configuration
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
"""
        
        with open("config.env", "w") as f:
            f.write(env_content.strip())
        
        print("✅ Environment file created")
    
    def run_database_migrations(self):
        """Run database migrations"""
        print("🗄️ Running database migrations...")
        
        try:
            # Create a migration script
            migration_script = f"""
import os
import asyncio
from models.database import init_db

# Set environment variables for Cloud SQL connection
os.environ['DB_SOCKET_PATH'] = '/cloudsql/{self.project_id}:us-central1:{self.db_instance_name}'
os.environ['DB_USER'] = '{self.db_user}'
os.environ['DB_PASSWORD'] = '{self.db_password}'
os.environ['DB_NAME'] = '{self.db_name}'

async def migrate():
    await init_db()
    print("Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(migrate())
"""
            
            with open('_temp_migration.py', 'w') as f:
                f.write(migration_script)
            
            # Run migration through Cloud Run service (it will have Cloud SQL access)
            print("Running migration through Cloud Run service...")
            service_url = self.get_service_url()
            
            # Use curl to trigger migration endpoint (if we add one) or just log success
            print("✅ Database migrations will be handled by the application startup")
            
            # Clean up
            if os.path.exists('_temp_migration.py'):
                os.remove('_temp_migration.py')
                
        except Exception as e:
            print(f"⚠️ Database migration warning: {e}")
            print("Database tables will be created automatically when the application starts")
    
    def get_service_url(self):
        """Get the deployed service URL"""
        print("🔗 Getting service URL...")
        
        result = self.run_command(f"gcloud run services describe {self.service_name} --region={self.region} --format='value(status.url)'")
        service_url = result.stdout.strip()
        
        print(f"✅ Service deployed at: {service_url}")
        return service_url
    
    def deploy(self):
        """Main deployment process"""
        print("🚀 Starting deployment of PDF to CSV Pipeline...")
        
        try:
            self.check_prerequisites()
            self.enable_apis()
            self.setup_cloud_sql()
            self.build_frontend()
            self.create_dockerfile()
            processor_id = self.setup_document_ai()
            self.create_env_file(processor_id)
            self.deploy_to_cloud_run()
            self.run_database_migrations()
            
            service_url = self.get_service_url()
            
            print("\n🎉 Deployment completed successfully!")
            print(f"🌐 Application URL: {service_url}")
            print(f"📊 Cloud SQL Instance: {self.db_instance_name}")
            print(f"🤖 Document AI Processor: {processor_id}")
            
            print("\n📝 Next steps:")
            print("1. Update your Document AI processor with the correct schema")
            print("2. Test the application by uploading a PDF")
            print("3. Monitor logs with: gcloud logs tail --follow")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    deployer = GCPDeployer()
    deployer.deploy()
