"""
Processing page - Upload PDFs and process them
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from database import db_manager
import streamlit as st

def render():
    """Render the processing page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("⚡ PDF Processing")
    st.markdown("Upload PDFs and process them with AI-powered extraction")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Check if a collection is selected
    if not st.session_state.get('selected_collection'):
        st.warning("Please select a collection first to process PDFs.")
        if st.button("Go to Collections"):
            st.session_state.current_page = "Collections"
            st.rerun()
        return
    
    # Get collection info
    try:
        collection = db_manager.get_collection_by_id(st.session_state.selected_collection)
        if not collection:
            st.error("Selected collection not found.")
            return
        
        st.info(f"Processing for collection: **{collection['collection_name']}** (Client: {collection['client_name']})")
    except Exception as e:
        st.error(f"Error loading collection: {e}")
        return
    
    # Processing configuration
    st.subheader("⚙️ Processing Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        group_size = st.slider("Group Size (PDFs per batch)", 10, 50, 25, 5)
        st.caption("Number of PDFs to process together")
    
    with col2:
        max_workers = st.selectbox("Concurrent Processing", [1, 2, 3, 4, 5], index=2)
        st.caption("Number of parallel processing threads")
    
    with col3:
        output_format = st.selectbox("Output Format", ["CSV", "Excel"], index=0)
        st.caption("Format for exported files")
    
    st.markdown("---")
    
    # File upload section
    st.subheader("📁 Upload PDF Files")
    
    uploaded_files = st.file_uploader(
        "Select PDF files to process",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload multiple PDF files. Each PDF should contain contact records."
    )
    
    if uploaded_files:
        st.success(f"📊 {len(uploaded_files)} files uploaded")
        
        # Display file information
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            total_size = sum(f.size for f in uploaded_files)
            st.metric("Total Size", f"{total_size / (1024*1024):.1f} MB")
        with col3:
            estimated_batches = (len(uploaded_files) + group_size - 1) // group_size
            st.metric("Estimated Batches", estimated_batches)
        with col4:
            estimated_records = len(uploaded_files) * 100  # Rough estimate
            st.metric("Estimated Records", f"{estimated_records:,}")
        
        # File preview
        with st.expander("📋 File Preview"):
            file_data = []
            for i, file in enumerate(uploaded_files[:10]):  # Show first 10 files
                file_data.append({
                    'File Name': file.name,
                    'Size (MB)': f"{file.size / (1024*1024):.2f}",
                    'Type': file.type
                })
            
            if file_data:
                import pandas as pd
                df = pd.DataFrame(file_data)
                st.dataframe(df, use_container_width=True)
                
                if len(uploaded_files) > 10:
                    st.caption(f"... and {len(uploaded_files) - 10} more files")
        
        st.markdown("---")
        
        # Processing options
        st.subheader("🚀 Start Processing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            batch_name = st.text_input(
                "Batch Name", 
                value=f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                help="Name for this processing batch"
            )
        
        with col2:
            enable_deduplication = st.checkbox("Enable Deduplication", value=True)
            st.caption("Remove duplicate records based on mobile numbers")
        
        # Validation
        if not batch_name:
            st.error("Please enter a batch name.")
        elif len(uploaded_files) == 0:
            st.error("Please upload at least one PDF file.")
        else:
            # Start processing button
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_files(uploaded_files, batch_name, group_size, max_workers, output_format, enable_deduplication)

def process_files(uploaded_files, batch_name, group_size, max_workers, output_format, enable_deduplication):
    """Process uploaded files"""
    try:
        # Create batch in database
        batch_id = db_manager.create_batch(
            collection_id=st.session_state.selected_collection,
            batch_name=batch_name,
            group_size=group_size
        )
        
        st.success(f"Created batch: {batch_name}")
        
        # Process files in groups
        total_files = len(uploaded_files)
        total_groups = (total_files + group_size - 1) // group_size
        
        st.info(f"Processing {total_files} files in {total_groups} groups of {group_size}")
        
        # Create progress containers
        progress_container = st.container()
        results_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process each group
            all_results = []
            for group_idx in range(total_groups):
                start_idx = group_idx * group_size
                end_idx = min(start_idx + group_size, total_files)
                group_files = uploaded_files[start_idx:end_idx]
                
                st.info(f"Processing group {group_idx + 1}/{total_groups} ({len(group_files)} files)")
                
                # Process this group
                group_results = process_group(group_files, batch_id, max_workers)
                all_results.extend(group_results)
                
                # Update progress
                progress = (group_idx + 1) / total_groups
                progress_bar.progress(progress)
                status_text.text(f"Completed group {group_idx + 1}/{total_groups}")
        
        with results_container:
            # Calculate final statistics
            successful_files = len([r for r in all_results if r['status'] == 'success'])
            total_raw_records = sum(r.get('raw_count', 0) for r in all_results if r['status'] == 'success')
            total_filtered_records = sum(r.get('filtered_count', 0) for r in all_results if r['status'] == 'success')
            duplicates_removed = total_raw_records - total_filtered_records
            
            # Display results
            st.subheader("📊 Processing Results")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Successful Files", successful_files)
            with col2:
                st.metric("Raw Records", f"{total_raw_records:,}")
            with col3:
                st.metric("Filtered Records", f"{total_filtered_records:,}")
            with col4:
                st.metric("Duplicates Removed", f"{duplicates_removed:,}")
            with col5:
                st.metric("Success Rate", f"{(successful_files/len(uploaded_files)*100):.1f}%")
            
            # Show detailed results
            if all_results:
                st.subheader("📋 Detailed Results")
                
                results_data = []
                for result in all_results:
                    results_data.append({
                        'File': result.get('file_id', 'Unknown'),
                        'Status': result['status'],
                        'Raw Records': result.get('raw_count', 0),
                        'Filtered Records': result.get('filtered_count', 0),
                        'Processing Time': f"{result.get('time', 0):.1f}s",
                        'Error': result.get('error', '')
                    })
                
                import pandas as pd
                df = pd.DataFrame(results_data)
                st.dataframe(df, use_container_width=True)
            
            # Export options
            st.subheader("💾 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📦 Download ZIP (All Files)", use_container_width=True):
                    create_and_download_zip(batch_id, output_format)
            
            with col2:
                if st.button("📄 Download Filtered CSV Only", use_container_width=True):
                    create_and_download_filtered_csv(batch_id)
            
            # Duplicate detection results
            if enable_deduplication:
                st.subheader("🔍 Duplicate Detection")
                
                try:
                    duplicates = db_manager.get_duplicate_records(batch_id)
                    if duplicates:
                        st.warning(f"Found {len(duplicates)} duplicate groups")
                        
                        # Show duplicate groups
                        for dup_group in duplicates[:5]:  # Show first 5 groups
                            with st.expander(f"Mobile: {dup_group['mobile']} ({dup_group['record_count']} records)"):
                                import json
                                records = json.loads(dup_group['records']) if isinstance(dup_group['records'], str) else dup_group['records']
                                dup_df = pd.DataFrame(records)
                                st.dataframe(dup_df, use_container_width=True)
                        
                        if len(duplicates) > 5:
                            st.caption(f"... and {len(duplicates) - 5} more duplicate groups")
                    else:
                        st.success("No duplicates found!")
                
                except Exception as e:
                    st.error(f"Error checking duplicates: {e}")
    
    except Exception as e:
        st.error(f"Error processing files: {e}")

def process_group(group_files, batch_id, max_workers):
    """Process a group of files"""
    import streamlit as st
    
    processor = st.session_state.processor
    
    # Create file records in database
    file_ids = []
    temp_paths = []
    
    for uploaded_file in group_files:
        temp_path = os.path.join(processor.temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        file_id = db_manager.create_file(
            batch_id, 
            uploaded_file.name, 
            temp_path, 
            uploaded_file.size
        )
        file_ids.append(file_id)
        temp_paths.append(temp_path)
    
    # Process files
    results = []
    for file_id, temp_path in zip(file_ids, temp_paths):
        result = processor.process_single_pdf(temp_path, batch_id, file_id)
        results.append(result)
    
    return results

def create_and_download_zip(batch_id, output_format):
    """Create and download ZIP file with all results"""
    try:
        # Get batch info
        batches = db_manager.get_batches_by_collection(st.session_state.selected_collection)
        batch = next((b for b in batches if b['id'] == batch_id), None)
        
        if not batch:
            st.error("Batch not found.")
            return
        
        # Get records for this batch
        records = db_manager.get_records_by_batch(batch_id, include_duplicates=False)
        
        if not records:
            st.warning("No records found for this batch.")
            return
        
        # Create ZIP file
        import zipfile
        import tempfile
        
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{batch['batch_name']}_results.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Create CSV files
            if records:
                import pandas as pd
                df = pd.DataFrame(records)
                
                # Raw records
                raw_csv_path = os.path.join(temp_dir, "raw_records.csv")
                df.to_csv(raw_csv_path, index=False)
                zipf.write(raw_csv_path, "raw_records.csv")
                
                # Filtered records (remove duplicates)
                filtered_df = df[~df['is_duplicate']]
                filtered_csv_path = os.path.join(temp_dir, "filtered_records.csv")
                filtered_df.to_csv(filtered_csv_path, index=False)
                zipf.write(filtered_csv_path, "filtered_records.csv")
                
                # Summary
                summary_data = {
                    'Total Records': len(df),
                    'Filtered Records': len(filtered_df),
                    'Duplicates Found': len(df[df['is_duplicate']]),
                    'Processing Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                summary_df = pd.DataFrame([summary_data])
                summary_csv_path = os.path.join(temp_dir, "summary.csv")
                summary_df.to_csv(summary_csv_path, index=False)
                zipf.write(summary_csv_path, "summary.csv")
        
        # Download
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📦 Download ZIP File",
                data=f.read(),
                file_name=f"{batch['batch_name']}_results.zip",
                mime="application/zip"
            )
        
        st.success("ZIP file created successfully!")
    
    except Exception as e:
        st.error(f"Error creating ZIP file: {e}")

def create_and_download_filtered_csv(batch_id):
    """Create and download filtered CSV only"""
    try:
        # Get batch info
        batches = db_manager.get_batches_by_collection(st.session_state.selected_collection)
        batch = next((b for b in batches if b['id'] == batch_id), None)
        
        if not batch:
            st.error("Batch not found.")
            return
        
        # Get filtered records
        records = db_manager.get_records_by_batch(batch_id, include_duplicates=False)
        
        if not records:
            st.warning("No records found for this batch.")
            return
        
        # Create CSV
        import pandas as pd
        df = pd.DataFrame(records)
        
        # Remove duplicate column for cleaner export
        if 'is_duplicate' in df.columns:
            df = df.drop('is_duplicate', axis=1)
        
        # Convert to CSV
        csv_data = df.to_csv(index=False)
        
        # Download
        st.download_button(
            label="📄 Download Filtered CSV",
            data=csv_data,
            file_name=f"{batch['batch_name']}_filtered.csv",
            mime="text/csv"
        )
        
        st.success("Filtered CSV ready for download!")
    
    except Exception as e:
        st.error(f"Error creating filtered CSV: {e}")
