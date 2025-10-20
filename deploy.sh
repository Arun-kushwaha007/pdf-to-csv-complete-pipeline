#!/bin/bash

# One-liner deployment script for Google Cloud Console
# Run this in Cloud Shell after cloning the repository

echo "🚀 PDF to CSV Pipeline - One-Click Deployment"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run from project root."
    echo "Make sure you've cloned the repository and are in the correct directory."
    exit 1
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Error: Not authenticated with gcloud."
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
echo "📋 Using project: $PROJECT_ID"

# Confirm deployment
echo ""
echo "This will deploy the PDF to CSV Pipeline to Google Cloud Platform."
echo "The deployment includes:"
echo "  • Cloud SQL PostgreSQL database"
echo "  • Cloud Run FastAPI backend"
echo "  • React frontend"
echo "  • Document AI processor"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Update project ID in deployment script
echo "🔧 Updating project configuration..."
sed -i "s/pdf2csv-475708/$PROJECT_ID/g" deploy_fastapi.py

# Run deployment
echo "🚀 Starting deployment..."
python deploy_fastapi.py

# Check if deployment was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Visit your application URL (shown above)"
    echo "2. Configure Document AI processor schema"
    echo "3. Test with a sample PDF"
    echo ""
    echo "📚 API Documentation: <your-url>/docs"
    echo "🔧 Monitor logs: gcloud logs tail --follow"
else
    echo ""
    echo "❌ Deployment failed. Check the error messages above."
    echo "Common solutions:"
    echo "  • Ensure billing is enabled"
    echo "  • Check API permissions"
    echo "  • Verify project ID is correct"
fi
