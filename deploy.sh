#!/bin/bash
# Simple deployment script for PDF to CSV Pipeline

echo "🚀 PDF to CSV Pipeline - Quick Deploy"
echo "====================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if project is set
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "❌ No GCP project set. Please run:"
    echo "   gcloud config set project YOUR-PROJECT-ID"
    exit 1
fi

echo "📋 Using project: $PROJECT_ID"

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated. Please run:"
    echo "   gcloud auth login"
    exit 1
fi

# Check if billing is enabled
if ! gcloud billing projects describe $PROJECT_ID &> /dev/null; then
    echo "❌ Billing not enabled for project $PROJECT_ID"
    echo "   Please enable billing in the Google Cloud Console:"
    echo "   https://console.cloud.google.com/billing"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Run the Python deployment script
echo "🚀 Starting deployment..."
python deploy_fastapi.py

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Check the Cloud Run service URL above"
echo "2. Test the application by uploading a PDF"
echo "3. Monitor logs with: gcloud logs tail --follow"