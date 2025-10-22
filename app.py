import streamlit as st
import os
import pandas as pd
import io
from dotenv import load_dotenv
from working_document_processor import WorkingDocumentProcessor
import tempfile
import zipfile
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('config.env')

# --- Configuration from environment variables ---
PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION', 'us')
PROCESSOR_ID = os.getenv('PROCESSOR_ID')
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
ENABLE_DUPLICATE_DETECTION = os.getenv('ENABLE_DUPLICATE_DETECTION', 'true').lower() == 'true'
DUPLICATE_KEY_FIELD = os.getenv('DUPLICATE_KEY_FIELD', 'mobile')

# Database configuration
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="PDF to CSV/Excel Processor")

st.title("📄 PDF to CSV/Excel Processor")
st.markdown("Upload your PDF files to extract contact information and download as CSV or Excel.")

# Sidebar for configuration and status
st.sidebar.header("Configuration & Status")
st.sidebar.write(f"**Project ID:** `{PROJECT_ID}`")
st.sidebar.write(f"**Location:** `{LOCATION}`")
st.sidebar.write(f"**Processor ID:** `{PROCESSOR_ID}`")
st.sidebar.write(f"**Credentials Path:** `{CREDENTIALS_PATH}`")

if not all([PROJECT_ID, LOCATION, PROCESSOR_ID, CREDENTIALS_PATH]):
    st.sidebar.error("🚨 Missing environment variables! Please check `config.env`.")
    st.stop()

# Initialize processor with database
db_config = None
if all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    db_config = {
        'host': DB_HOST,
        'port': int(DB_PORT),
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }

try:
    processor = WorkingDocumentProcessor(
        project_id=PROJECT_ID,
        location=LOCATION,
        processor_id=PROCESSOR_ID,
        credentials_path=CREDENTIALS_PATH,
        db_config=db_config
    )
    if db_config:
        st.sidebar.success("✅ Document Processor + Database Initialized!")
    else:
        st.sidebar.success("✅ Document Processor Initialized! (No DB)")
except Exception as e:
    st.sidebar.error(f"❌ Failed to initialize Document Processor: {e}")
    st.stop()

uploaded_files = st.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("Process Files"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF file.")
            st.stop()

        all_raw_records = []
        all_filtered_records = []
        processed_file_count = 0
        total_files = len(uploaded_files)
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing file {i+1}/{total_files}: {uploaded_file.name}...")
            progress_bar.progress((i + 1) / total_files)

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                # Process the document
                result = processor.process_document(tmp_file_path)
                if result:
                    # Add file name to each record
                    for record in result['raw_records']:
                        record['file_name'] = uploaded_file.name
                    for record in result['filtered_records']:
                        record['file_name'] = uploaded_file.name
                        
                    all_raw_records.extend(result['raw_records'])
                    all_filtered_records.extend(result['filtered_records'])
                processed_file_count += 1
                os.remove(tmp_file_path) # Clean up temp file

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
                logger.error(f"Error processing {uploaded_file.name}: {e}", exc_info=True)
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)

        status_text.success(f"✅ Processed {processed_file_count} of {total_files} files.")

        # Save to database if connected
        if db_config and (all_raw_records or all_filtered_records):
            session_name = f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            for i, uploaded_file in enumerate(uploaded_files):
                # Get records for this specific file
                file_raw = [r for r in all_raw_records if r.get('file_name') == uploaded_file.name]
                file_filtered = [r for r in all_filtered_records if r.get('file_name') == uploaded_file.name]
                
                if file_raw or file_filtered:
                    processor.save_to_database(
                        raw_records=file_raw,
                        filtered_records=file_filtered,
                        file_name=uploaded_file.name,
                        session_name=session_name if i == 0 else None
                    )
            st.success("💾 Data saved to database!")

        # Display results
        if all_raw_records or all_filtered_records:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Raw Records (Unfiltered)")
                if all_raw_records:
                    raw_df = pd.DataFrame(all_raw_records)
                    st.dataframe(raw_df)
                    st.write(f"**Total Raw Records:** {len(all_raw_records)}")
                else:
                    st.info("No raw records found.")
            
            with col2:
                st.subheader("✅ Filtered Records (Validated)")
                if all_filtered_records:
                    filtered_df = pd.DataFrame(all_filtered_records)
                    st.dataframe(filtered_df)
                    st.write(f"**Total Filtered Records:** {len(all_filtered_records)}")
                else:
                    st.info("No filtered records found.")

            # Download options
            st.subheader("📥 Download Results")

            # Create ZIP file with both raw and filtered data
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add raw CSV
                if all_raw_records:
                    raw_csv = io.StringIO()
                    raw_df.to_csv(raw_csv, index=False)
                    zip_file.writestr("raw_data.csv", raw_csv.getvalue())
                
                # Add filtered CSV
                if all_filtered_records:
                    filtered_csv = io.StringIO()
                    filtered_df.to_csv(filtered_csv, index=False)
                    zip_file.writestr("filtered_data.csv", filtered_csv.getvalue())
                
                # Add summary
                summary_data = {
                    'Metric': ['Total Files Processed', 'Raw Records', 'Filtered Records', 'Success Rate'],
                    'Value': [
                        processed_file_count,
                        len(all_raw_records),
                        len(all_filtered_records),
                        f"{(len(all_filtered_records)/len(all_raw_records)*100):.1f}%" if all_raw_records else "0%"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_csv = io.StringIO()
                summary_df.to_csv(summary_csv, index=False)
                zip_file.writestr("summary.csv", summary_csv.getvalue())

            # Download buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📦 Download ZIP (All Data)",
                    data=zip_buffer.getvalue(),
                    file_name="pdf_extraction_results.zip",
                    mime="application/zip",
                )
            
            with col2:
                if all_raw_records:
                    raw_csv_buffer = io.StringIO()
                    raw_df.to_csv(raw_csv_buffer, index=False)
                    st.download_button(
                        label="📄 Download Raw CSV",
                        data=raw_csv_buffer.getvalue(),
                        file_name="raw_data.csv",
                        mime="text/csv",
                    )
            
            with col3:
                if all_filtered_records:
                    filtered_csv_buffer = io.StringIO()
                    filtered_df.to_csv(filtered_csv_buffer, index=False)
                    st.download_button(
                        label="✅ Download Filtered CSV",
                        data=filtered_csv_buffer.getvalue(),
                        file_name="filtered_data.csv",
                        mime="text/csv",
                    )

            # Excel download
            if all_filtered_records:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # Filtered data sheet
                    filtered_df.to_excel(writer, sheet_name='Filtered Data', index=False)
                    
                    # Raw data sheet
                    if all_raw_records:
                        raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
                    
                    # Duplicate detection
                    if ENABLE_DUPLICATE_DETECTION and 'mobile' in filtered_df.columns:
                        duplicates = processor.detect_duplicates(all_filtered_records)
                        if duplicates:
                            duplicates_df = pd.DataFrame(duplicates)
                            duplicates_df.to_excel(writer, sheet_name='Duplicates', index=False)
                            st.warning(f"⚠️ Found {len(duplicates)} duplicate records based on mobile number.")
                        else:
                            st.info("✅ No duplicate records found.")
                    
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Total Files Processed', 'Raw Records', 'Filtered Records', 'Success Rate'],
                        'Value': [
                            processed_file_count,
                            len(all_raw_records),
                            len(all_filtered_records),
                            f"{(len(all_filtered_records)/len(all_raw_records)*100):.1f}%" if all_raw_records else "0%"
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

                st.download_button(
                    label="📊 Download Excel",
                    data=excel_buffer.getvalue(),
                    file_name="pdf_extraction_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.warning("No records extracted from the uploaded files.")

# Database Records Section
if db_config:
    st.markdown("---")
    st.header("🗄️ Database Records")
    
    # Database stats
    stats = processor.get_database_stats()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Raw Records", stats.get('raw_records', 0))
        with col2:
            st.metric("Filtered Records", stats.get('filtered_records', 0))
        with col3:
            st.metric("Files Processed", stats.get('files_processed', 0))
        with col4:
            st.metric("Unique Mobiles", stats.get('unique_mobiles', 0))
    
    # Toggle between raw and filtered
    col1, col2 = st.columns([1, 3])
    with col1:
        view_type = st.selectbox("View Records", ["Filtered", "Raw"], index=0)
    with col2:
        limit = st.slider("Number of records to show", 10, 1000, 100)
    
    # Load and display records
    if st.button(f"Load {view_type} Records from Database"):
        record_type = view_type.lower()
        records = processor.get_records_from_database(record_type, limit)
        
        if records:
            df = pd.DataFrame(records)
            
            # Remove internal database fields for display
            display_columns = [col for col in df.columns if col not in ['id', 'created_at', 'updated_at']]
            display_df = df[display_columns]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download options for database records
            st.subheader(f"📥 Download {view_type} Records")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv_buffer = io.StringIO()
                display_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label=f"📄 Download {view_type} CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{record_type}_records.csv",
                    mime="text/csv",
                )
            
            with col2:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    display_df.to_excel(writer, sheet_name=f'{view_type} Records', index=False)
                
                st.download_button(
                    label=f"📊 Download {view_type} Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"{record_type}_records.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.info(f"No {view_type} records found in database.")

# Footer
st.markdown("---")
st.markdown("**Note:** Raw records contain all extracted data without validation. Filtered records contain only validated data with proper name format, valid mobile numbers, and addresses with street numbers.")