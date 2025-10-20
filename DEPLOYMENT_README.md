# PDF to CSV Pipeline - Deployment Guide

## Overview

This guide will help you deploy the PDF to CSV Pipeline application on Google Cloud Platform. The application provides a comprehensive solution for processing PDF documents and extracting contact information using AI-powered Document AI.

## Prerequisites

Before starting the deployment, ensure you have the following:

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed and configured
3. **Docker** installed on your local machine
4. **Python 3.8+** installed
5. **Administrative access** to the GCP project

## Quick Start

### Option 1: Automated Deployment (Recommended)

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd pdf-to-csv-complete-pipeline
   ```

2. **Run the deployment script**:
   ```bash
   python deploy.py
   ```

3. **Follow the interactive prompts** to configure your deployment

### Option 2: Manual Deployment

If you prefer to deploy manually, follow the steps below:

## Manual Deployment Steps

### 1. Set Up Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudsql.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Create Cloud SQL Database

```bash
# Create Cloud SQL instance
gcloud sql instances create pdf2csv-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup \
    --enable-ip-alias \
    --network=default

# Create database
gcloud sql databases create pdf2csv_db --instance=pdf2csv-db

# Create user
gcloud sql users create pdf2csv_user --instance=pdf2csv-db --password=your-secure-password
```

### 3. Set Up Document AI

1. Go to [Google Cloud Console - Document AI](https://console.cloud.google.com/ai/document-ai)
2. Create a new processor
3. Choose "Form Parser" or "Invoice Parser" based on your needs
4. Note down the processor ID

### 4. Configure Environment Variables

Update `config.env` with your settings:

```env
# Google Cloud Project Configuration
PROJECT_ID=your-project-id
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path-to-your-service-account-key.json

# Database Configuration
DB_HOST=pdf2csv-db.your-project-id.us-central1.gcp
DB_PORT=5432
DB_NAME=pdf2csv_db
DB_USER=pdf2csv_user
DB_PASSWORD=your-secure-password
DB_SSL=true
DB_SOCKET_PATH=/cloudsql/your-project-id:us-central1:pdf2csv-db

# Document AI Processor ID
CUSTOM_PROCESSOR_ID=your-processor-id
```

### 5. Build and Deploy

```bash
# Build Docker image
docker build -t gcr.io/$PROJECT_ID/pdf2csv-pipeline .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/pdf2csv-pipeline

# Deploy to Cloud Run
gcloud run deploy pdf2csv-pipeline \
    --image gcr.io/$PROJECT_ID/pdf2csv-pipeline \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars PROJECT_ID=$PROJECT_ID \
    --set-env-vars LOCATION=us-central1
```

### 6. Set Up Database Schema

```bash
# Connect to database and run schema
gcloud sql connect pdf2csv-db --user=pdf2csv_user --database=pdf2csv_db < database_schema.sql
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PROJECT_ID` | Google Cloud Project ID | Yes | - |
| `LOCATION` | Document AI location | Yes | `us` |
| `DB_HOST` | Cloud SQL host | Yes | - |
| `DB_PORT` | Database port | Yes | `5432` |
| `DB_NAME` | Database name | Yes | `pdf2csv_db` |
| `DB_USER` | Database user | Yes | - |
| `DB_PASSWORD` | Database password | Yes | - |
| `CUSTOM_PROCESSOR_ID` | Document AI processor ID | Yes | - |

### Database Schema

The application uses the following main tables:

- **collections**: Store client collections and metadata
- **batches**: Store processing batches
- **files**: Store individual PDF files
- **records**: Store extracted contact records
- **duplicate_groups**: Track duplicate records
- **processing_logs**: Store processing logs
- **export_history**: Track export operations

## Features

### 1. Collections Management
- Create and manage client collections
- Archive/unarchive collections
- Track collection metadata and statistics

### 2. PDF Processing
- Upload multiple PDFs
- AI-powered text extraction using Document AI
- Configurable grouping (25 PDFs per group by default)
- Real-time processing progress

### 3. Data Management
- Automatic duplicate detection based on mobile numbers
- Data validation and cleaning
- Inline editing and review capabilities
- Export in multiple formats (CSV, Excel, ZIP)

### 4. Export Options
- Quick export for individual batches
- Custom export with field selection
- Grouped exports by collection or batch
- Multiple file formats and encoding options

### 5. Monitoring and Logging
- Processing logs and audit trail
- Export history tracking
- System health monitoring
- Error reporting and debugging

## Usage

### 1. Access the Application

After deployment, access your application at the Cloud Run URL provided during deployment.

### 2. Create Your First Collection

1. Go to the "Collections" page
2. Click "Create New Collection"
3. Fill in collection details (name, client, notes)
4. Save the collection

### 3. Process PDFs

1. Go to the "Processing" page
2. Select a collection
3. Upload PDF files
4. Configure processing settings
5. Start processing

### 4. Review and Export Data

1. Go to the "Collections" page
2. View your processed data
3. Review duplicates and invalid records
4. Export data in your preferred format

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Cloud SQL instance is running
   - Verify database credentials
   - Ensure Cloud SQL Admin API is enabled

2. **Document AI Processing Failed**
   - Verify processor ID is correct
   - Check Document AI API is enabled
   - Ensure service account has proper permissions

3. **Application Won't Start**
   - Check Cloud Run logs
   - Verify environment variables
   - Ensure all required APIs are enabled

### Logs and Debugging

- **Cloud Run Logs**: Available in Google Cloud Console
- **Database Logs**: Check Cloud SQL logs
- **Application Logs**: Available in the History page

## Security Considerations

1. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Restrict access to authorized IPs

2. **Application Security**
   - Use service accounts with minimal permissions
   - Enable audit logging
   - Regular security updates

3. **Data Privacy**
   - Data is stored in your GCP project
   - No data is shared with third parties
   - Implement data retention policies

## Cost Optimization

1. **Cloud SQL**
   - Use appropriate instance size
   - Enable automatic storage increase
   - Monitor usage and adjust as needed

2. **Cloud Run**
   - Set appropriate memory and CPU limits
   - Use request-based scaling
   - Monitor concurrent instances

3. **Document AI**
   - Process files in batches
   - Use appropriate processor types
   - Monitor API usage

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review Cloud Run and Cloud SQL logs
3. Contact your system administrator
4. Create an issue in the repository

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

### Version 2.0.0
- Complete UI redesign with collections management
- Database integration with Cloud SQL
- Enhanced export options
- Improved duplicate detection
- Archive/unarchive functionality
- Comprehensive logging and monitoring

### Version 1.0.0
- Initial release with basic PDF processing
- Streamlit-based UI
- Document AI integration
- CSV export functionality
