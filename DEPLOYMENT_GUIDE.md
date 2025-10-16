# Deployment Guide - Enhanced PDF to CSV Converter

## 🚀 Pre-Deployment Checklist

### 1. Google Cloud Setup
- [ ] Google Cloud Project created
- [ ] Document AI API enabled
- [ ] Custom Document AI processor created and trained
- [ ] Service account created with Document AI permissions
- [ ] Service account key downloaded

### 2. Environment Configuration
- [ ] Update `config.env` with your project details
- [ ] Set correct `PROJECT_ID`
- [ ] Set correct `CUSTOM_PROCESSOR_ID`
- [ ] Verify `LOCATION` matches your processor region
- [ ] Place service account JSON file in project directory

### 3. Dependencies Installation
```bash
pip install -r requirements.txt
```

### 4. Testing
```bash
python test_processor.py
```
All tests should pass before deployment.

## 🌐 Local Development

### Running the Application
```bash
streamlit run app.py
```

### Configuration Options
- **Batch Size**: 10-50 PDFs per batch (default: 40)
- **Output Format**: CSV or Excel
- **Records per Group**: 10-50 records per file (default: 25)
- **Concurrent Workers**: 1-5 parallel threads (default: 3)

## ☁️ Google Cloud Run Deployment

### 1. Prepare for Deployment
```bash
# Install Google Cloud CLI
# Authenticate with your account
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Build and Deploy
```bash
# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pdf2csv-converter

# Deploy to Cloud Run
gcloud run deploy pdf2csv-converter \
  --image gcr.io/YOUR_PROJECT_ID/pdf2csv-converter \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10
```

### 3. Environment Variables
Set these in Cloud Run:
```
PROJECT_ID=your-project-id
LOCATION=us
CUSTOM_PROCESSOR_ID=your-processor-id
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json
```

### 4. Service Account Setup
- Create a service account with Document AI permissions
- Download the JSON key
- Add it to your container or use Workload Identity

## 📊 Performance Optimization

### Recommended Settings
- **Memory**: 2-4GB for large batches
- **CPU**: 2-4 cores for concurrent processing
- **Timeout**: 3600 seconds (1 hour) for large batches
- **Max Instances**: 5-10 depending on usage

### Batch Processing Guidelines
- **Small batches (10-20 PDFs)**: 1-2 workers
- **Medium batches (20-40 PDFs)**: 2-3 workers
- **Large batches (40+ PDFs)**: 3-5 workers

## 🔧 Troubleshooting

### Common Issues

#### 1. "No entities found"
**Cause**: Document AI processor not configured correctly
**Solution**:
- Verify processor ID in config
- Check processor is deployed and active
- Ensure document format matches training data

#### 2. Low extraction accuracy
**Cause**: Poor document quality or processor training
**Solution**:
- Retrain Document AI processor with more samples
- Improve document quality (higher resolution, better contrast)
- Verify entity type names match configuration

#### 3. Memory issues
**Cause**: Processing too many files simultaneously
**Solution**:
- Reduce batch size
- Decrease concurrent workers
- Increase Cloud Run memory allocation

#### 4. API rate limits
**Cause**: Too many concurrent requests
**Solution**:
- Reduce concurrent workers
- Add delays between batches
- Check Google Cloud quotas

### Monitoring and Logging

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Cloud Run Logs
```bash
gcloud logs read --service=pdf2csv-converter --limit=50
```

#### Performance Metrics
Monitor these metrics:
- Processing time per file
- Memory usage
- API request count
- Error rates

## 📈 Scaling Considerations

### Horizontal Scaling
- Use Cloud Run's automatic scaling
- Set appropriate min/max instances
- Monitor concurrent request limits

### Vertical Scaling
- Increase memory for large documents
- Add CPU cores for faster processing
- Consider longer timeouts for large batches

### Cost Optimization
- Use preemptible instances for non-critical workloads
- Set appropriate instance limits
- Monitor usage patterns

## 🔒 Security Best Practices

### Service Account Permissions
- Use least privilege principle
- Only grant necessary Document AI permissions
- Rotate service account keys regularly

### Data Privacy
- Process data in the same region when possible
- Use encryption in transit and at rest
- Implement data retention policies

### Access Control
- Use IAM for user access control
- Enable audit logging
- Monitor access patterns

## 📋 Maintenance

### Regular Tasks
- [ ] Monitor processing accuracy
- [ ] Update Document AI processor with new samples
- [ ] Review and optimize batch sizes
- [ ] Check for dependency updates
- [ ] Monitor costs and usage

### Updates
- Test changes in development first
- Use blue-green deployment for production
- Keep backup of working configurations
- Document all changes

## 🆘 Support

### Getting Help
1. Check this deployment guide
2. Review Google Cloud Document AI documentation
3. Check Cloud Run logs for errors
4. Run the test suite to verify functionality

### Emergency Procedures
- Rollback to previous version if needed
- Check service account permissions
- Verify Document AI processor status
- Monitor Google Cloud status page

## 📞 Contact Information

For technical support or questions about this deployment:
- Review the README.md for detailed feature documentation
- Check the test_processor.py for functionality verification
- Ensure all environment variables are correctly set
