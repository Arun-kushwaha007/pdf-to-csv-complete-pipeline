# Enhanced PDF to CSV Converter

A scalable, high-accuracy AI-powered system that extracts structured data from PDF documents and exports it to CSV/Excel format using Google Cloud Document AI.

## 🚀 New Features

### Enhanced Data Extraction
- **Complete Field Extraction**: Extracts all contact information including:
  - Name (with smart parsing into First Name and Last Name)
  - Mobile phone numbers
  - Landline phone numbers
  - Addresses
  - Email addresses
  - Date of Birth
  - Last Seen Date

### Smart Processing
- **Intelligent Name Parsing**: Uses the `nameparser` library to accurately split full names
- **Phone-based Deduplication**: Removes duplicate records based on phone numbers (mobile or landline)
- **Dual Output Types**: 
  - **Raw Data**: All extracted records before deduplication
  - **Filtered Data**: Clean records after deduplication

### Batch Processing
- **Configurable Batch Size**: Process 40 PDFs at a time (configurable)
- **Concurrent Processing**: Multi-threaded processing for optimal performance
- **Grouped Outputs**: Results grouped in sets of 25 records per file (configurable)

### Multiple Output Formats
- **CSV Format**: Standard comma-separated values
- **Excel Format**: Formatted Excel files with headers and auto-sized columns

## 📋 Requirements

### System Requirements
- Python 3.8+
- Google Cloud Platform account
- Document AI API enabled
- Custom Document AI processor configured

### Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies:
- `google-cloud-documentai>=2.21.0`
- `streamlit==1.28.0`
- `pandas>=2.0.0`
- `openpyxl>=3.1.2`
- `nameparser==1.1.2`

## ⚙️ Configuration

### Environment Variables
Update your `config.env` file:

```env
# Google Cloud Configuration
PROJECT_ID=your-project-id
LOCATION=us
CUSTOM_PROCESSOR_ID=your-processor-id
GOOGLE_APPLICATION_CREDENTIALS=path-to-service-account.json

# Processing Configuration
BATCH_SIZE=40
GROUP_SIZE=25
MAX_CONCURRENT_REQUESTS=5
```

### Document AI Processor Setup
1. Create a custom Document AI processor in Google Cloud Console
2. Train it to recognize the following entity types:
   - `name` - Full names
   - `mobile` - Mobile phone numbers
   - `landline` - Landline phone numbers
   - `address` - Addresses
   - `email` - Email addresses
   - `date_of_birth` - Date of birth
   - `last_seen_date` - Last seen date

## 🚀 Usage

### Running the Application
```bash
streamlit run app.py
```

### Web Interface Features
- **Sidebar Configuration**: Adjust batch size, output format, and processing options
- **File Upload**: Drag and drop multiple PDF files
- **Real-time Progress**: Live progress tracking with detailed statistics
- **Download Results**: Get processed data in organized zip files

### Processing Options
- **Batch Size**: Number of PDFs to process simultaneously (10-50)
- **Output Format**: Choose between CSV or Excel
- **Records per Group**: Number of records per output file (10-50)
- **Concurrent Workers**: Number of parallel processing threads (1-5)

## 📊 Output Structure

### Download Package Contents
```
pdf_extraction_[format]_[timestamp].zip
├── raw_group_1.csv/xlsx          # Raw data (before deduplication)
├── raw_group_2.csv/xlsx
├── filtered_group_1.csv/xlsx     # Filtered data (after deduplication)
├── filtered_group_2.csv/xlsx
└── processing_summary.csv        # Detailed processing statistics
```

### Data Schema
Each record contains:
- `first_name` - Parsed first name
- `last_name` - Parsed last name
- `mobile` - Mobile phone number (cleaned)
- `landline` - Landline phone number (cleaned)
- `address` - Full address
- `email` - Email address (validated)
- `date_of_birth` - Date of birth
- `last_seen_date` - Last seen date

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_processor.py
```

Tests include:
- Name parsing accuracy
- Phone number cleaning
- Deduplication logic
- Output format generation
- Field extraction and grouping

## 📈 Performance

### Expected Performance
- **Processing Speed**: ~2-5 files per second (depending on complexity)
- **Accuracy**: Near 100% for properly formatted documents
- **Scalability**: Handles hundreds of PDFs with thousands of records
- **Memory Usage**: Optimized for large batch processing

### Optimization Features
- Concurrent processing with configurable workers
- Efficient memory management for large datasets
- Smart batching to prevent API rate limits
- Automatic retry logic for failed requests

## 🔧 Advanced Configuration

### Custom Field Mapping
Modify `working_document_processor.py` to adjust field extraction:

```python
# Customize entity type matching
names = [e['value'] for e in entities if 'name' in e['type'].lower()]
mobiles = [e['value'] for e in entities if 'mobile' in e['type'].lower()]
```

### Deduplication Rules
Customize deduplication logic in `_deduplicate_records()`:

```python
# Current: Phone-based deduplication
# Modify to use different criteria (email, name+address, etc.)
```

### Output Formatting
Customize Excel formatting in `save_excel()`:

```python
# Adjust column widths, colors, fonts
cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
```

## 🚨 Troubleshooting

### Common Issues

1. **No entities found**
   - Verify Document AI processor ID
   - Check document format matches training data
   - Ensure processor is deployed and active

2. **Low extraction accuracy**
   - Retrain Document AI processor with more samples
   - Verify entity type names match configuration
   - Check document quality and resolution

3. **Memory issues with large batches**
   - Reduce batch size
   - Decrease concurrent workers
   - Process files in smaller groups

4. **API rate limits**
   - Reduce concurrent requests
   - Add delays between batches
   - Check Google Cloud quotas

### Logging
Enable detailed logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Changelog

### Version 2.0 (Current)
- ✅ Enhanced field extraction (7 fields)
- ✅ Smart name parsing with nameparser
- ✅ Phone-based deduplication
- ✅ Dual output types (raw/filtered)
- ✅ Batch processing (40 PDFs)
- ✅ Multiple output formats (CSV/Excel)
- ✅ Grouped outputs (25 records per file)
- ✅ Enhanced UI with real-time progress
- ✅ Comprehensive testing suite

### Version 1.0 (Previous)
- Basic PDF to CSV conversion
- Simple field extraction (4 fields)
- Individual file processing
- CSV output only

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test suite to identify problems
3. Review Google Cloud Document AI documentation
4. Check processor training and deployment status

## 📄 License

This project is proprietary software developed for client use.
