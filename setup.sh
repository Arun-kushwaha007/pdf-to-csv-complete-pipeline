#!/bin/bash

# Cloud Console Setup Script
# Run this first to prepare your environment

echo "🔧 Setting up Google Cloud Console for PDF to CSV Pipeline"
echo "========================================================="

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "🔐 Authenticating with Google Cloud..."
    gcloud auth login
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
echo "📋 Current project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Set up service account
echo "👤 Setting up service account..."
SERVICE_ACCOUNT="pdf2csv-service@$PROJECT_ID.iam.gserviceaccount.com"

# Check if service account exists
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create pdf2csv-service \
        --display-name="PDF to CSV Service Account" \
        --description="Service account for PDF to CSV Pipeline"
else
    echo "Service account already exists."
fi

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/documentai.apiUser" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.admin" \
    --quiet

# Create service account key
echo "🔐 Creating service account key..."
gcloud iam service-accounts keys create pdf2csv-key.json \
    --iam-account=$SERVICE_ACCOUNT

# Update config.env
echo "📝 Updating configuration..."
if [ -f "config.env" ]; then
    sed -i "s/PROJECT_ID=.*/PROJECT_ID=$PROJECT_ID/" config.env
    sed -i "s/GOOGLE_APPLICATION_CREDENTIALS=.*/GOOGLE_APPLICATION_CREDENTIALS=.\/pdf2csv-key.json/" config.env
else
    echo "❌ config.env not found. Please ensure you're in the project directory."
    exit 1
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  • Project ID: $PROJECT_ID"
echo "  • Service Account: $SERVICE_ACCOUNT"
echo "  • APIs enabled: Cloud Build, Cloud Run, Cloud SQL, Document AI, Storage"
echo "  • Service account key: pdf2csv-key.json"
echo "  • Configuration updated: config.env"
echo ""
echo "🚀 Ready to deploy! Run: ./deploy.sh"
echo ""
echo "📚 Or for manual deployment: python deploy_fastapi.py"
