# PDF to CSV Pipeline - FastAPI + React

A modern, robust web application for processing PDF documents and extracting contact information using Google Cloud Document AI.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python start_local.py
```

### Deploy to Google Cloud
```bash
# Run the deployment script
python deploy_fastapi.py
```

## 📁 Project Structure

```
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── config.env             # Environment configuration
├── deploy_fastapi.py      # Deployment script
├── start_local.py         # Local development script
├── .dockerignore          # Docker ignore file
├── api/                   # API endpoints
│   ├── collections.py
│   ├── files.py
│   ├── records.py
│   └── exports.py
├── models/                # Database models
│   ├── database.py
│   └── schemas.py
├── services/              # Business logic
│   ├── document_processor.py
│   ├── duplicate_detector.py
│   ├── export_service.py
│   └── ...
├── utils/                 # Utilities
│   ├── config.py
│   └── storage.py
└── frontend/              # React frontend
    ├── src/
    ├── public/
    └── package.json
```

## 🔧 Configuration

Update `config.env` with your settings:
- Google Cloud project ID
- Database credentials
- Document AI processor ID

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🌐 Frontend

The React frontend is built and served by the FastAPI backend.
- Modern UI with dark/light theme
- Real-time processing updates
- File upload with drag & drop
- Records management
- Export functionality

## 🚀 Deployment

The deployment script handles:
- Google Cloud API enablement
- Cloud SQL setup
- Frontend build
- Docker container creation
- Cloud Run deployment

## 📖 Full Documentation

See `README_FASTAPI.md` for complete documentation.
