# 🚀 Deploy PDF to CSV Pipeline on Google Cloud Platform

**Complete deployment guide for Google Cloud Console**

## ⚡ Quick Start (2 minutes)

### Option 1: One-Click Deployment
```bash
# 1. Clone repository
git clone <your-repo-url>
cd pdf-to-csv-complete-pipeline

# 2. Setup environment
./setup.sh

# 3. Deploy everything
./deploy.sh
```

### Option 2: Manual Deployment
```bash
# 1. Clone repository
git clone <your-repo-url>
cd pdf-to-csv-complete-pipeline

# 2. Update project ID in deploy_fastapi.py (line 15)
# Change: self.project_id = "pdf2csv-475708"
# To: self.project_id = "your-project-id"

# 3. Deploy
python deploy_fastapi.py
```

---

## 📋 Prerequisites

- ✅ Google Cloud Project with billing enabled
- ✅ Cloud Shell access (recommended) or local gcloud CLI
- ✅ Project permissions (Owner or Editor)

---

## 🎯 What Gets Deployed

The deployment creates:

| Service | Purpose | Cost |
|---------|---------|------|
| **Cloud Run** | FastAPI backend + React frontend | ~$0-5/month |
| **Cloud SQL** | PostgreSQL database | ~$10-20/month |
| **Document AI** | PDF processing | Pay per document |
| **Cloud Build** | Container building | Pay per build |
| **Cloud Storage** | File storage | Pay per GB |

**Total estimated cost: $10-30/month** (depending on usage)

---

## 🔧 Detailed Setup

### Step 1: Open Google Cloud Console
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select your project
3. Open Cloud Shell (terminal icon in top bar)

### Step 2: Clone Repository
```bash
git clone https://github.com/your-username/pdf-to-csv-complete-pipeline.git
cd pdf-to-csv-complete-pipeline
```

### Step 3: Run Setup Script
```bash
./setup.sh
```

This script will:
- ✅ Authenticate with Google Cloud
- ✅ Enable required APIs
- ✅ Create service account
- ✅ Set up permissions
- ✅ Create service account key
- ✅ Update configuration

### Step 4: Deploy Application
```bash
./deploy.sh
```

This script will:
- ✅ Create Cloud SQL PostgreSQL instance
- ✅ Build React frontend
- ✅ Create Docker container
- ✅ Deploy to Cloud Run
- ✅ Set up Document AI processor

---

## 🎉 After Deployment

You'll see output like:
```
🎉 Deployment completed successfully!
🌐 Application URL: https://pdf2csv-api-xxxxx-uc.a.run.app
📊 Cloud SQL Instance: pdf2csv-db
🤖 Document AI Processor: xxxxx
```

### Test Your Application
1. **Visit the URL** - Your React app is live!
2. **API Documentation** - Visit `<your-url>/docs`
3. **Upload a PDF** - Test the processing pipeline

---

## 🔧 Configuration

### Environment Variables
The deployment sets these automatically:
```env
PROJECT_ID=your-project-id
DB_HOST=/cloudsql/your-project:us-central1:pdf2csv-db
DB_NAME=pdf2csv_db
DB_USER=pdf2csv_user
DB_PASSWORD=@Sharing1234
CUSTOM_PROCESSOR_ID=your-processor-id
```

### Document AI Processor
After deployment:
1. Go to Document AI in Google Cloud Console
2. Find your processor
3. Update the schema for contact extraction
4. Test with sample PDFs

---

## 🚨 Troubleshooting

### Common Issues

**1. "Project not found"**
```bash
gcloud config set project your-project-id
gcloud auth login
```

**2. "Permission denied"**
```bash
# Enable APIs manually
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable documentai.googleapis.com
```

**3. "Frontend build failed"**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run build
```

**4. "Database connection failed"**
```bash
# Check Cloud SQL instance
gcloud sql instances list
gcloud sql instances describe pdf2csv-db
```

### View Logs
```bash
# View all logs
gcloud logs tail --follow

# View specific service logs
gcloud logs tail --follow --filter="resource.labels.service_name=pdf2csv-api"
```

### Restart Service
```bash
# Restart Cloud Run service
gcloud run services update pdf2csv-api --region=us-central1
```

---

## 📊 Monitoring

### View Resources
```bash
# List all services
gcloud run services list

# List databases
gcloud sql instances list

# List Document AI processors
gcloud documentai processors list --location=us
```

### Monitor Performance
1. Go to Cloud Console → Cloud Run
2. Click on your service
3. View metrics, logs, and performance

---

## 🔄 Updates

### Update Application
```bash
# Make code changes
# Then redeploy
python deploy_fastapi.py
```

### Update Frontend Only
```bash
cd frontend
npm run build
# Frontend is automatically served by FastAPI
```

---

## 🗑️ Cleanup

### Delete Everything
```bash
# Delete Cloud Run service
gcloud run services delete pdf2csv-api --region=us-central1

# Delete Cloud SQL instance
gcloud sql instances delete pdf2csv-db

# Delete Document AI processor
gcloud documentai processors delete your-processor-id --location=us

# Delete service account
gcloud iam service-accounts delete pdf2csv-service@your-project-id.iam.gserviceaccount.com
```

---

## 📚 Additional Resources

- **API Documentation**: `<your-url>/docs`
- **ReDoc**: `<your-url>/redoc`
- **Google Cloud Console**: [console.cloud.google.com](https://console.cloud.google.com)
- **Cloud Run Documentation**: [cloud.google.com/run](https://cloud.google.com/run)
- **Document AI Documentation**: [cloud.google.com/document-ai](https://cloud.google.com/document-ai)

---

## 🆘 Support

If you encounter issues:

1. **Check logs**: `gcloud logs tail --follow`
2. **Verify billing**: Ensure billing is enabled
3. **Check permissions**: Ensure you have Owner/Editor role
4. **Review quotas**: Check if you've hit any service limits

**Happy Deploying!** 🚀
