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
        
        # Save uploaded files to temp directory (preserve upload order)
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            pdf_paths.append(temp_path)
        
        # Process in batches (we still break into batches of PDFs for parallel/quotas)
        all_results = []
        total_batches = math.ceil(total_files / batch_size)
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_files)
            batch_files = pdf_paths[start_idx:end_idx]
            
            st.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # We will collect results in a map keyed by filename so we can append them
            # back in the same order as batch_files (preserve upload order for grouping).
            batch_results_map = {}
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_pdf = {executor.submit(self.process_single_pdf, path): path for path in batch_files}
                
                completed = 0
                
                for future in as_completed(future_to_pdf):
                    path = future_to_pdf[future]
                    result = future.result()
                    batch_results_map[os.path.basename(path)] = result  # key by filename
                    
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
            
            # Append batch results in the original upload order (batch_files order)
            for path in batch_files:
                filename = os.path.basename(path)
                if filename in batch_results_map:
                    all_results.append(batch_results_map[filename])
                else:
                    # In case something odd happened, append a no_data placeholder
                    all_results.append({
                        'status': 'error',
                        'file': filename,
                        'error': 'Missing result (executor failure)',
                        'raw_records': [],
                        'filtered_records': [],
                        'raw_count': 0,
                        'filtered_count': 0,
                        'time': 0
                    })
        
        return all_results


    def create_download_zip(self, results, output_format='csv', group_size=25):
        """
        Build a ZIP where grouping is done by PDFs per sheet (group_size = PDFs per sheet).
        Each group includes all records from those PDFs combined into a single file.
        """
        zip_path = os.path.join(self.temp_dir, "results.zip")
        
        # results is expected to be a list where each entry corresponds to one PDF (in upload order)
        # We'll chunk results into groups of `group_size` PDFs, and for each group create a file
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            total_pdfs = len(results)
            total_groups = math.ceil(total_pdfs / group_size) if group_size > 0 else 1
            
            for grp_idx in range(total_groups):
                start_idx = grp_idx * group_size
                end_idx = min(start_idx + group_size, total_pdfs)
                grp_results = results[start_idx:end_idx]  # slice of results for these PDFs
                
                # Collect combined raw and filtered records for this pdf-group
                combined_raw = []
                combined_filtered = []
                summary_rows = []
                
                for res in grp_results:
                    if res['status'] == 'success':
                        combined_raw.extend(res.get('raw_records', []))
                        combined_filtered.extend(res.get('filtered_records', []))
                    
                    # Add to group summary (helps trace which PDFs contributed)
                    summary_rows.append({
                        'file': res.get('file', ''),
                        'status': res.get('status', ''),
                        'raw_records': res.get('raw_count', 0),
                        'filtered_records': res.get('filtered_count', 0),
                        'processing_time': res.get('time', 0),
                        'error': res.get('error', '')
                    })
                
                # Write combined files for this group
                group_label = f"group_pdfs_{grp_idx + 1}_files_{start_idx + 1}_to_{end_idx}"
                
                # Raw
                if combined_raw:
                    if output_format.lower() == 'excel':
                        excel_path = os.path.join(self.temp_dir, f"raw_{group_label}.xlsx")
                        self.processor.save_excel(combined_raw, excel_path)
                        zipf.write(excel_path, os.path.basename(excel_path))
                    else:
                        csv_path = os.path.join(self.temp_dir, f"raw_{group_label}.csv")
                        self.processor.save_csv(combined_raw, csv_path)
                        zipf.write(csv_path, os.path.basename(csv_path))
                
                # Filtered
                if combined_filtered:
                    if output_format.lower() == 'excel':
                        excel_path = os.path.join(self.temp_dir, f"filtered_{group_label}.xlsx")
                        self.processor.save_excel(combined_filtered, excel_path)
                        zipf.write(excel_path, os.path.basename(excel_path))
                    else:
                        csv_path = os.path.join(self.temp_dir, f"filtered_{group_label}.csv")
                        self.processor.save_csv(combined_filtered, csv_path)
                        zipf.write(csv_path, os.path.basename(csv_path))
                
                # Group summary file (per-group)
                summary_df = pd.DataFrame(summary_rows)
                summary_path = os.path.join(self.temp_dir, f"summary_{group_label}.csv")
                summary_df.to_csv(summary_path, index=False)
                zipf.write(summary_path, os.path.basename(summary_path))
            
            # Global processing summary (all PDFs)
            global_summary = []
            for result in results:
                global_summary.append({
                    'file': result.get('file', ''),
                    'status': result.get('status', ''),
                    'raw_records': result.get('raw_count', 0),
                    'filtered_records': result.get('filtered_count', 0),
                    'processing_time': result.get('time', 0),
                    'error': result.get('error', '')
                })
            global_summary_df = pd.DataFrame(global_summary)
            global_summary_path = os.path.join(self.temp_dir, "processing_summary.csv")
            global_summary_df.to_csv(global_summary_path, index=False)
            zipf.write(global_summary_path, "processing_summary.csv")
        
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
    group_size = st.sidebar.slider("PDFs per Sheet (group size in PDFs)", 1, 50, 25, 1)
    
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
                    st.markdown(f"• **Grouped by {group_size} PDFs per file (all records from those PDFs combined)**")

                    
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
