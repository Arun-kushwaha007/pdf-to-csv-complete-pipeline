#!/usr/bin/env python3
"""
PDF to CSV Pipeline - Deployment Script
Automated deployment script for Google Cloud Platform
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class GCPDeployer:
    def __init__(self):
        self.project_id = None
        self.region = "us-central1"
        self.service_name = "pdf2csv-pipeline"
        self.db_instance_name = "pdf2csv-db"
        self.db_tier = "db-f1-micro"  # Smallest tier for cost efficiency
        
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        required_tools = ['gcloud', 'docker']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
                print(f"✅ {tool} is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                print(f"❌ {tool} is not installed")
        
        if missing_tools:
            print(f"\n❌ Missing required tools: {', '.join(missing_tools)}")
            print("Please install the missing tools and try again.")
            print("\nInstallation instructions:")
            print("- gcloud: https://cloud.google.com/sdk/docs/install")
            print("- docker: https://docs.docker.com/get-docker/")
            return False
        
        return True
    
    def authenticate_gcp(self):
        """Authenticate with Google Cloud"""
        print("\n🔐 Authenticating with Google Cloud...")
        
        try:
            # Check if already authenticated
            result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                print(f"✅ Already authenticated as: {result.stdout.strip()}")
                return True
            
            # Authenticate
            print("Please authenticate with Google Cloud...")
            subprocess.run(['gcloud', 'auth', 'login'], check=True)
            print("✅ Authentication successful")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_project_info(self):
        """Get and set project information"""
        print("\n📋 Setting up project...")
        
        try:
            # Get current project
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True)
            current_project = result.stdout.strip()
            
            if current_project:
                print(f"Current project: {current_project}")
                use_current = input("Use current project? (y/n): ").lower().strip()
                
                if use_current == 'y':
                    self.project_id = current_project
                    return True
            
            # List available projects
            print("\nAvailable projects:")
            result = subprocess.run(['gcloud', 'projects', 'list', '--format=table(projectId,name)'], 
                                  capture_output=True, text=True)
            print(result.stdout)
            
            # Get project ID from user
            self.project_id = input("\nEnter project ID: ").strip()
            
            if not self.project_id:
                print("❌ Project ID is required")
                return False
            
            # Set project
            subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], check=True)
            print(f"✅ Project set to: {self.project_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to set project: {e}")
            return False
    
    def enable_apis(self):
        """Enable required Google Cloud APIs"""
        print("\n🔌 Enabling required APIs...")
        
        apis = [
            'cloudsql.googleapis.com',
            'documentai.googleapis.com',
            'run.googleapis.com',
            'cloudbuild.googleapis.com',
            'artifactregistry.googleapis.com'
        ]
        
        for api in apis:
            try:
                print(f"Enabling {api}...")
                subprocess.run(['gcloud', 'services', 'enable', api], check=True)
                print(f"✅ {api} enabled")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to enable {api}: {e}")
                return False
        
        return True
    
    def create_cloud_sql_instance(self):
        """Create Cloud SQL instance"""
        print("\n🗄️ Creating Cloud SQL instance...")
        
        try:
            # Check if instance already exists
            result = subprocess.run(['gcloud', 'sql', 'instances', 'describe', self.db_instance_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Cloud SQL instance {self.db_instance_name} already exists")
                return True
            
            # Create instance
            cmd = [
                'gcloud', 'sql', 'instances', 'create', self.db_instance_name,
                '--database-version=POSTGRES_14',
                '--tier', self.db_tier,
                '--region', self.region,
                '--storage-type=SSD',
                '--storage-size=10GB',
                '--storage-auto-increase',
                '--backup',
                '--enable-ip-alias',
                '--network=default'
            ]
            
            print("Creating Cloud SQL instance (this may take several minutes)...")
            subprocess.run(cmd, check=True)
            print(f"✅ Cloud SQL instance {self.db_instance_name} created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create Cloud SQL instance: {e}")
            return False
    
    def create_database(self):
        """Create database and user"""
        print("\n📊 Setting up database...")
        
        try:
            # Create database
            subprocess.run(['gcloud', 'sql', 'databases', 'create', 'pdf2csv_db', 
                          '--instance', self.db_instance_name], check=True)
            print("✅ Database 'pdf2csv_db' created")
            
            # Create user
            db_password = input("Enter database password (min 8 characters): ").strip()
            if len(db_password) < 8:
                print("❌ Password must be at least 8 characters")
                return False
            
            subprocess.run(['gcloud', 'sql', 'users', 'create', 'pdf2csv_user', 
                          '--instance', self.db_instance_name, '--password', db_password], check=True)
            print("✅ Database user 'pdf2csv_user' created")
            
            # Save password to config
            self.save_db_config(db_password)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup database: {e}")
            return False
    
    def save_db_config(self, db_password):
        """Save database configuration"""
        config = {
            'DB_HOST': f'{self.db_instance_name}.{self.project_id}.{self.region}.gcp',
            'DB_PORT': '5432',
            'DB_NAME': 'pdf2csv_db',
            'DB_USER': 'pdf2csv_user',
            'DB_PASSWORD': db_password,
            'DB_SSL': 'true',
            'DB_SOCKET_PATH': f'/cloudsql/{self.project_id}:{self.region}:{self.db_instance_name}'
        }
        
        # Update config.env
        config_path = Path('config.env')
        if config_path.exists():
            with open(config_path, 'r') as f:
                content = f.read()
            
            for key, value in config.items():
                content = content.replace(f'{key}=your-{key.lower().replace("_", "-")}', f'{key}={value}')
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("✅ Database configuration saved to config.env")
    
    def setup_document_ai(self):
        """Setup Document AI processor"""
        print("\n📄 Setting up Document AI...")
        
        try:
            # Check if processor already exists
            result = subprocess.run(['gcloud', 'ai', 'custom-jobs', 'list', '--region', self.region], 
                                  capture_output=True, text=True)
            
            print("Please create a Document AI processor manually:")
            print("1. Go to https://console.cloud.google.com/ai/document-ai")
            print("2. Create a new processor")
            print("3. Choose 'Form Parser' or 'Invoice Parser'")
            print("4. Note down the processor ID")
            
            processor_id = input("Enter Document AI processor ID: ").strip()
            
            if not processor_id:
                print("❌ Processor ID is required")
                return False
            
            # Update config.env with processor ID
            config_path = Path('config.env')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                
                content = content.replace('CUSTOM_PROCESSOR_ID=e3a0679d2b58c372', f'CUSTOM_PROCESSOR_ID={processor_id}')
                
                with open(config_path, 'w') as f:
                    f.write(content)
                
                print("✅ Document AI processor ID saved to config.env")
                return True
            
        except Exception as e:
            print(f"❌ Failed to setup Document AI: {e}")
            return False
    
    def build_and_deploy(self):
        """Build and deploy the application"""
        print("\n🚀 Building and deploying application...")
        
        try:
            # Build Docker image
            print("Building Docker image...")
            subprocess.run(['docker', 'build', '-t', f'gcr.io/{self.project_id}/{self.service_name}', '.'], check=True)
            print("✅ Docker image built")
            
            # Push to Google Container Registry
            print("Pushing image to Google Container Registry...")
            subprocess.run(['docker', 'push', f'gcr.io/{self.project_id}/{self.service_name}'], check=True)
            print("✅ Image pushed to GCR")
            
            # Deploy to Cloud Run
            print("Deploying to Cloud Run...")
            cmd = [
                'gcloud', 'run', 'deploy', self.service_name,
                '--image', f'gcr.io/{self.project_id}/{self.service_name}',
                '--platform', 'managed',
                '--region', self.region,
                '--allow-unauthenticated',
                '--memory', '2Gi',
                '--cpu', '2',
                '--max-instances', '10',
                '--set-env-vars', f'PROJECT_ID={self.project_id}',
                '--set-env-vars', f'LOCATION={self.region}'
            ]
            
            subprocess.run(cmd, check=True)
            print("✅ Application deployed to Cloud Run")
            
            # Get service URL
            result = subprocess.run(['gcloud', 'run', 'services', 'describe', self.service_name, 
                                   '--region', self.region, '--format', 'value(status.url)'], 
                                  capture_output=True, text=True)
            
            service_url = result.stdout.strip()
            print(f"🌐 Service URL: {service_url}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy application: {e}")
            return False
    
    def setup_database_schema(self):
        """Setup database schema"""
        print("\n📋 Setting up database schema...")
        
        try:
            # Get Cloud SQL connection name
            connection_name = f'{self.project_id}:{self.region}:{self.db_instance_name}'
            
            # Run schema setup
            subprocess.run(['gcloud', 'sql', 'connect', self.db_instance_name, 
                          '--user', 'pdf2csv_user', '--database', 'pdf2csv_db'], 
                         input=open('database_schema.sql').read(), text=True, check=True)
            
            print("✅ Database schema created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup database schema: {e}")
            print("Please run the database_schema.sql file manually on your Cloud SQL instance")
            return False
    
    def run_deployment(self):
        """Run the complete deployment process"""
        print("🚀 PDF to CSV Pipeline - Deployment Script")
        print("=" * 50)
        
        steps = [
            ("Check Prerequisites", self.check_prerequisites),
            ("Authenticate GCP", self.authenticate_gcp),
            ("Setup Project", self.get_project_info),
            ("Enable APIs", self.enable_apis),
            ("Create Cloud SQL Instance", self.create_cloud_sql_instance),
            ("Setup Database", self.create_database),
            ("Setup Document AI", self.setup_document_ai),
            ("Build and Deploy", self.build_and_deploy),
            ("Setup Database Schema", self.setup_database_schema)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*20} {step_name} {'='*20}")
            if not step_func():
                print(f"\n❌ Deployment failed at step: {step_name}")
                return False
        
        print("\n🎉 Deployment completed successfully!")
        print("\nNext steps:")
        print("1. Update your config.env with the correct database password")
        print("2. Test the application by visiting the Cloud Run URL")
        print("3. Create your first collection and start processing PDFs")
        
        return True

def main():
    """Main function"""
    deployer = GCPDeployer()
    
    try:
        success = deployer.run_deployment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
