import streamlit as st
import os
import zipfile
import tempfile
import time
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import math

# Import your working processor
from working_document_processor import WorkingDocumentProcessor

# Configure for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="PDF to CSV Converter",
    page_icon="📄",
    layout="wide"
)

class ProductionProcessor:
    def __init__(self):
        self.project_id = os.getenv('PROJECT_ID', 'pdf2csv-converter-tool')
        self.location = os.getenv('LOCATION', 'us')
        self.processor_id = os.getenv('CUSTOM_PROCESSOR_ID', 'e3a0679d2b58c372')
        self.processor = WorkingDocumentProcessor(self.project_id, self.location)
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_single_pdf(self, pdf_path: str) -> dict:
        try:
            start_time = time.time()
            result = self.processor.process_document(pdf_path, self.processor_id)
            processing_time = time.time() - start_time
            
            raw_records = result.get('raw_records', [])
            filtered_records = result.get('filtered_records', [])
            
            if raw_records or filtered_records:
                pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
                
                return {
                    'status': 'success',
                    'file': os.path.basename(pdf_path),
                    'raw_records': raw_records,
                    'filtered_records': filtered_records,
                    'raw_count': len(raw_records),
                    'filtered_count': len(filtered_records),
                    'time': processing_time
                }
            else:
                return {
                    'status': 'no_data',
                    'file': os.path.basename(pdf_path),
                    'raw_records': [],
                    'filtered_records': [],
                    'raw_count': 0,
                    'filtered_count': 0,
                    'time': processing_time
                }
        except Exception as e:
            return {
                'status': 'error',
                'file': os.path.basename(pdf_path),
                'error': str(e),
                'raw_records': [],
                'filtered_records': [],
                'raw_count': 0,
                'filtered_count': 0,
                'time': 0
            }
    
    def process_batch(self, uploaded_files, max_workers=3, batch_size=40):
        total_files = len(uploaded_files)
        results = []
        pdf_paths = []
        
        # Save uploaded files to temp directory
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            pdf_paths.append(temp_path)
        
        # Process in batches
        all_results = []
        total_batches = math.ceil(total_files / batch_size)
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_files)
            batch_files = pdf_paths[start_idx:end_idx]
            
            st.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_pdf = {executor.submit(self.process_single_pdf, path): path for path in batch_files}
                
                completed = 0
                batch_results = []
                
                for future in as_completed(future_to_pdf):
                    result = future.result()
                    batch_results.append(result)
                    all_results.append(result)
                    
                    completed += 1
                    progress = completed / len(batch_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Batch {batch_idx + 1}: {completed}/{len(batch_files)}")
                    
                    if result['status'] == 'success':
                        st.success(f"{result['file']}: {result['raw_count']} raw, {result['filtered_count']} filtered ({result['time']:.1f}s)")
                    elif result['status'] == 'no_data':
                        st.warning(f"{result['file']}: No valid data found")
                    else:
                        st.error(f"{result['file']}: {result['error']}")
        
        return all_results
    
    def create_download_zip(self, results, output_format='csv', group_size=25):
        zip_path = os.path.join(self.temp_dir, "results.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Collect all raw and filtered records
            all_raw_records = []
            all_filtered_records = []
            
            for result in results:
                if result['status'] == 'success':
                    all_raw_records.extend(result['raw_records'])
                    all_filtered_records.extend(result['filtered_records'])
            
            # Create grouped outputs
            if all_raw_records:
                self._create_grouped_outputs(all_raw_records, zipf, "raw", output_format, group_size)
            
            if all_filtered_records:
                self._create_grouped_outputs(all_filtered_records, zipf, "filtered", output_format, group_size)
            
            # Create summary
            summary_data = []
            for result in results:
                summary_data.append({
                    'file': result['file'],
                    'status': result['status'],
                    'raw_records': result.get('raw_count', 0),
                    'filtered_records': result.get('filtered_count', 0),
                    'processing_time': result.get('time', 0),
                    'error': result.get('error', '')
                })
            
            summary = pd.DataFrame(summary_data)
            summary_path = os.path.join(self.temp_dir, "processing_summary.csv")
            summary.to_csv(summary_path, index=False)
            zipf.write(summary_path, "processing_summary.csv")
        
        return zip_path
    
    def _create_grouped_outputs(self, records, zipf, data_type, output_format, group_size):
        """Create grouped outputs for raw or filtered data"""
        total_groups = math.ceil(len(records) / group_size)
        
        for group_idx in range(total_groups):
            start_idx = group_idx * group_size
            end_idx = min(start_idx + group_size, len(records))
            group_records = records[start_idx:end_idx]
            
            if output_format.lower() == 'excel':
                # Create Excel file with multiple sheets
                excel_path = os.path.join(self.temp_dir, f"{data_type}_group_{group_idx + 1}.xlsx")
                self.processor.save_excel(group_records, excel_path)
                zipf.write(excel_path, f"{data_type}_group_{group_idx + 1}.xlsx")
            else:
                # Create CSV file
                csv_path = os.path.join(self.temp_dir, f"{data_type}_group_{group_idx + 1}.csv")
                self.processor.save_csv(group_records, csv_path)
                zipf.write(csv_path, f"{data_type}_group_{group_idx + 1}.csv")

def main():
    st.title("📄 PDF to CSV Batch Processor")
    st.markdown("**Enhanced AI-powered document processing with Google Cloud Document AI**")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    if 'processor' not in st.session_state:
        with st.spinner("🔧 Initializing processor..."):
            try:
                st.session_state.processor = ProductionProcessor()
                st.success("✅ Processor initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize: {e}")
                st.stop()
    
    processor = st.session_state.processor
    
    # Configuration options
    batch_size = st.sidebar.slider("Batch Size (PDFs per batch)", 10, 50, 40, 5)
    max_workers = st.sidebar.selectbox("Concurrent Processing", [1, 2, 3, 4, 5], index=2)
    output_format = st.sidebar.selectbox("Output Format", ["CSV", "Excel"], index=0)
    group_size = st.sidebar.slider("Records per Group", 10, 50, 25, 5)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Features:**")
    st.sidebar.markdown("✅ Extract all contact fields")
    st.sidebar.markdown("✅ Smart name parsing")
    st.sidebar.markdown("✅ Phone-based deduplication")
    st.sidebar.markdown("✅ Raw & filtered outputs")
    st.sidebar.markdown("✅ Batch processing")
    
    # Main content
    st.header("📁 Upload PDF Files")
    uploaded_files = st.file_uploader(
        "Select PDF files (each containing ~100 records)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload multiple PDF files. Each PDF should contain approximately 100 contact records."
    )
    
    if uploaded_files:
        st.success(f"📊 {len(uploaded_files)} files uploaded")
        
        # Display file information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            st.metric("Estimated Records", len(uploaded_files) * 100)
        with col3:
            st.metric("Processing Batches", math.ceil(len(uploaded_files) / batch_size))
        
        # Processing options
        st.subheader("🚀 Processing Options")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Batch Size:** {batch_size} PDFs per batch")
            st.info(f"**Output Format:** {output_format}")
        with col2:
            st.info(f"**Concurrent Workers:** {max_workers}")
            st.info(f"**Records per Group:** {group_size}")
        
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            st.header("⚡ Processing Results")
            
            # Create progress containers
            progress_container = st.container()
            results_container = st.container()
            
            with progress_container:
                start_time = time.time()
                results = processor.process_batch(uploaded_files, max_workers, batch_size)
                total_time = time.time() - start_time
            
            with results_container:
                # Calculate statistics
                successful = len([r for r in results if r['status'] == 'success'])
                total_raw_records = sum(r.get('raw_count', 0) for r in results if r['status'] == 'success')
                total_filtered_records = sum(r.get('filtered_count', 0) for r in results if r['status'] == 'success')
                duplicates_removed = total_raw_records - total_filtered_records
                
                # Display metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Successful Files", successful)
                with col2:
                    st.metric("Raw Records", total_raw_records)
                with col3:
                    st.metric("Filtered Records", total_filtered_records)
                with col4:
                    st.metric("Duplicates Removed", duplicates_removed)
                with col5:
                    st.metric("Processing Time", f"{total_time:.1f}s")
                
                # Processing speed
                if total_time > 0:
                    st.metric("Processing Speed", f"{len(uploaded_files)/total_time:.1f} files/s")
                
                # Results summary
                if successful > 0:
                    st.header("📥 Download Results")
                    
                    # Create download files
                    zip_path = processor.create_download_zip(results, output_format.lower(), group_size)
                    
                    # Download button
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label=f"🎉 Download {output_format} Files",
                            data=f.read(),
                            file_name=f"pdf_extraction_{output_format.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    # Show what's included
                    st.info(f"📦 **Download includes:**")
                    st.markdown(f"• **Raw data files** (before deduplication)")
                    st.markdown(f"• **Filtered data files** (after deduplication)")
                    st.markdown(f"• **Processing summary** with detailed statistics")
                    st.markdown(f"• **Grouped by {group_size} records** per file")
                    
                    # Show sample of extracted data
                    if results and results[0]['status'] == 'success':
                        st.subheader("📋 Sample Extracted Data")
                        sample_records = results[0]['filtered_records'][:5]  # Show first 5 records
                        if sample_records:
                            sample_df = pd.DataFrame(sample_records)
                            st.dataframe(sample_df, use_container_width=True)
                else:
                    st.warning("⚠️ No files were processed successfully. Please check your PDF format and processor configuration.")

if __name__ == "__main__":
    main()
