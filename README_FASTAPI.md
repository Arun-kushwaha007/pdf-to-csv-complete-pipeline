# PDF to CSV Pipeline - FastAPI + React

A modern, robust web application for processing PDF documents and extracting contact information using Google Cloud Document AI. Built with FastAPI backend and React frontend.

## 🚀 Features

### Core Functionality
- **PDF Processing**: Upload multiple PDF files and extract contact information using AI
- **Collections Management**: Organize data by client and project
- **Duplicate Detection**: Automatically detect and manage duplicate records
- **Export Options**: Download data in CSV, Excel, or ZIP formats
- **Real-time Processing**: Live progress tracking with WebSocket updates

### User Interface
- **Modern React UI**: Clean, responsive design with dark/light theme toggle
- **Dashboard**: Overview of collections, processing jobs, and statistics
- **File Upload**: Drag-and-drop interface with progress tracking
- **Records Management**: View, edit, validate, and manage extracted records
- **Export Management**: Create and download exports with custom options

### Technical Features
- **FastAPI Backend**: High-performance async API with automatic documentation
- **PostgreSQL Database**: Robust data storage with Cloud SQL
- **Google Cloud Integration**: Document AI, Cloud Storage, Cloud Run
- **Real-time Updates**: Live processing status and notifications
- **Error Handling**: Comprehensive error handling and user feedback

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  Google Cloud   │
│                 │    │                 │    │                 │
│ • Dashboard      │◄──►│ • REST API      │◄──►│ • Document AI   │
│ • File Upload    │    │ • WebSockets    │    │ • Cloud SQL     │
│ • Records Mgmt   │    │ • Background    │    │ • Cloud Storage │
│ • Export Mgmt    │    │   Processing    │    │ • Cloud Run     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Robust relational database
- **Google Cloud Document AI**: AI-powered document processing
- **Pydantic**: Data validation and settings management

### Frontend
- **React 18**: Modern React with hooks and context
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication
- **React Hot Toast**: Toast notifications
- **Lucide React**: Beautiful icons

### Infrastructure
- **Google Cloud Run**: Serverless container platform
- **Google Cloud SQL**: Managed PostgreSQL database
- **Google Cloud Storage**: Object storage
- **Docker**: Containerization

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud SDK
- Docker (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdf-to-csv-complete-pipeline
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements_fastapi.txt
   
   # Set up environment variables
   cp config.env.example config.env
   # Edit config.env with your settings
   
   # Run database migrations
   python -c "from models.database import init_db; import asyncio; asyncio.run(init_db())"
   
   # Start the backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup**
   ```bash
   # Install dependencies
   cd frontend
   npm install
   
   # Start development server
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🚀 Deployment

### Automated Deployment
```bash
# Run the deployment script
python deploy_fastapi.py
```

### Manual Deployment

1. **Build and deploy to Cloud Run**
   ```bash
   # Build frontend
   cd frontend && npm run build && cd ..
   
   # Build and push container
   gcloud builds submit --tag gcr.io/pdf2csv-475708/pdf2csv-api
   
   # Deploy to Cloud Run
   gcloud run deploy pdf2csv-api \
     --image gcr.io/pdf2csv-475708/pdf2csv-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

2. **Set up Cloud SQL**
   ```bash
   # Create Cloud SQL instance
   gcloud sql instances create pdf2csv-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1
   
   # Create database and user
   gcloud sql databases create pdf2csv_db --instance=pdf2csv-db
   gcloud sql users create postgres --instance=pdf2csv-db --password=your-password
   ```

## 📊 API Documentation

The FastAPI backend provides automatic API documentation:

- **Swagger UI**: http://your-domain/docs
- **ReDoc**: http://your-domain/redoc
- **OpenAPI Schema**: http://your-domain/openapi.json

### Key Endpoints

- `GET /api/collections` - List collections
- `POST /api/files/upload` - Upload and process PDFs
- `GET /api/records` - Get extracted records
- `POST /api/exports/generate` - Create export
- `GET /api/exports/{id}/download` - Download export

## 🎨 UI Components

### Pages
- **Dashboard**: Overview and quick actions
- **Collections**: Manage data collections
- **Processing**: Upload and process PDFs
- **Records**: View and manage extracted data
- **Exports**: Create and download exports
- **Settings**: Configure application settings

### Features
- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live processing status
- **Bulk Operations**: Select and manage multiple records
- **Advanced Filtering**: Filter records by various criteria

## 🔧 Configuration

### Environment Variables

```env
# Google Cloud
PROJECT_ID=your-project-id
CUSTOM_PROCESSOR_ID=your-processor-id
GOOGLE_APPLICATION_CREDENTIALS=path-to-credentials.json

# Database
DB_HOST=your-db-host
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# Processing
DEFAULT_GROUP_SIZE=25
MAX_CONCURRENT_JOBS=5

# Export
DEFAULT_EXPORT_FORMAT=csv
DEFAULT_ENCODING=utf-8
```

## 📈 Performance

- **Concurrent Processing**: Process multiple PDFs simultaneously
- **Background Jobs**: Non-blocking file processing
- **Database Optimization**: Efficient queries and indexing
- **Caching**: Redis caching for frequently accessed data
- **CDN**: Static asset delivery via Cloud CDN

## 🔒 Security

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control
- **Data Validation**: Pydantic model validation
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS Configuration**: Proper cross-origin settings

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Cloud SQL instance status
   - Verify connection string and credentials
   - Ensure Cloud SQL proxy is running

2. **Document AI Processing Failed**
   - Verify processor ID and permissions
   - Check PDF file format and size
   - Review Document AI quotas

3. **Frontend Build Failed**
   - Check Node.js version (18+)
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

### Logs

```bash
# View Cloud Run logs
gcloud logs tail --follow --filter="resource.type=cloud_run_revision"

# View specific service logs
gcloud logs tail --follow --filter="resource.labels.service_name=pdf2csv-api"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at `/docs`

## 🔄 Migration from Streamlit

If migrating from the previous Streamlit version:

1. **Data Migration**: Export data from old database
2. **Configuration**: Update environment variables
3. **Deployment**: Use new deployment script
4. **Testing**: Verify all functionality works

The new FastAPI + React version provides:
- Better performance and scalability
- Modern UI/UX
- Real-time updates
- Better error handling
- Mobile responsiveness
- Improved maintainability
