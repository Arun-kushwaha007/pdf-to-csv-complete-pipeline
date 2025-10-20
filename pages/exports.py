"""
Exports page - Download and manage exports
"""

import streamlit as st
import pandas as pd
import zipfile
import tempfile
import os
from datetime import datetime
from database import db_manager

def render():
    """Render the exports page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("💾 Export Management")
    st.markdown("Download processed data in various formats")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for different export options
    tab1, tab2, tab3 = st.tabs(["Quick Export", "Custom Export", "Export History"])
    
    with tab1:
        render_quick_export()
    
    with tab2:
        render_custom_export()
    
    with tab3:
        render_export_history()

def render_quick_export():
    """Render quick export options"""
    st.subheader("⚡ Quick Export")
    
    try:
        # Get collections
        collections = db_manager.get_collections(status='active', limit=50)
        
        if not collections:
            st.info("No active collections found.")
            return
        
        # Collection selection
        collection_options = {f"{c['collection_name']} ({c['client_name']})": c['id'] for c in collections}
        selected_collection_name = st.selectbox("Select Collection", list(collection_options.keys()))
        
        if not selected_collection_name:
            return
        
        selected_collection_id = collection_options[selected_collection_name]
        collection = db_manager.get_collection_by_id(selected_collection_id)
        
        # Get batches for selected collection
        batches = db_manager.get_batches_by_collection(selected_collection_id)
        
        if not batches:
            st.info("No batches found for this collection.")
            return
        
        # Batch selection
        batch_options = {f"{b['batch_name']} ({b['status']})": b['id'] for b in batches}
        selected_batch_name = st.selectbox("Select Batch", list(batch_options.keys()))
        
        if not selected_batch_name:
            return
        
        selected_batch_id = batch_options[selected_batch_name]
        batch = next((b for b in batches if b['id'] == selected_batch_id), None)
        
        if not batch:
            st.error("Selected batch not found.")
            return
        
        # Show batch info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", batch.get('total_records', 0))
        with col2:
            st.metric("Filtered Records", batch.get('filtered_records', 0))
        with col3:
            st.metric("Duplicates Found", batch.get('duplicates_found', 0))
        with col4:
            st.metric("Status", batch['status'].title())
        
        st.markdown("---")
        
        # Export options
        st.subheader("📦 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "ZIP (All Files)"])
            include_duplicates = st.checkbox("Include Duplicates", value=False)
        
        with col2:
            encoding = st.selectbox("File Encoding", ["UTF-8", "Latin-1"])
            delimiter = st.selectbox("CSV Delimiter", [",", ";", "\t"])
        
        # Export button
        if st.button("🚀 Generate Export", type="primary", use_container_width=True):
            generate_export(selected_batch_id, export_format, include_duplicates, encoding, delimiter)

def render_custom_export():
    """Render custom export options"""
    st.subheader("🎛️ Custom Export")
    
    try:
        # Get collections
        collections = db_manager.get_collections(limit=100)
        
        if not collections:
            st.info("No collections found.")
            return
        
        # Multi-collection selection
        collection_names = [f"{c['collection_name']} ({c['client_name']})" for c in collections]
        selected_collections = st.multiselect("Select Collections", collection_names)
        
        if not selected_collections:
            st.info("Please select at least one collection.")
            return
        
        # Get selected collection IDs
        selected_collection_ids = []
        for selected_name in selected_collections:
            for collection in collections:
                if f"{collection['collection_name']} ({collection['client_name']})" == selected_name:
                    selected_collection_ids.append(collection['id'])
                    break
        
        # Export configuration
        st.subheader("⚙️ Export Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "ZIP (All Files)"], key="custom_format")
            group_by = st.selectbox("Group By", ["Collection", "Batch", "None"])
            include_metadata = st.checkbox("Include Metadata", value=True)
        
        with col2:
            encoding = st.selectbox("File Encoding", ["UTF-8", "Latin-1"], key="custom_encoding")
            delimiter = st.selectbox("CSV Delimiter", [",", ";", "\t"], key="custom_delimiter")
            date_range = st.checkbox("Filter by Date Range")
        
        # Date range filter
        if date_range:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
        else:
            start_date = end_date = None
        
        # Field selection
        st.subheader("📋 Field Selection")
        
        # Get sample records to show available fields
        sample_records = []
        for collection_id in selected_collection_ids[:1]:  # Get sample from first collection
            batches = db_manager.get_batches_by_collection(collection_id)
            if batches:
                sample_records = db_manager.get_records_by_batch(batches[0]['id'], limit=1)
                break
        
        if sample_records:
            available_fields = list(sample_records[0].keys())
            selected_fields = st.multiselect(
                "Select Fields to Export",
                available_fields,
                default=available_fields
            )
        else:
            st.warning("No records found to determine available fields.")
            selected_fields = []
        
        # Export button
        if st.button("🚀 Generate Custom Export", type="primary", use_container_width=True):
            if not selected_fields:
                st.error("Please select at least one field to export.")
            else:
                generate_custom_export(
                    selected_collection_ids, 
                    export_format, 
                    group_by, 
                    include_metadata, 
                    encoding, 
                    delimiter,
                    selected_fields,
                    start_date,
                    end_date
                )
    
    except Exception as e:
        st.error(f"Error setting up custom export: {e}")

def render_export_history():
    """Render export history"""
    st.subheader("📊 Export History")
    
    try:
        # Get export history
        exports = db_manager.get_export_history(limit=100)
        
        if not exports:
            st.info("No exports found.")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_type_filter = st.selectbox("Export Type", ["All", "zip_all", "filtered_csv", "raw_csv", "excel"])
        
        with col2:
            status_filter = st.selectbox("Status", ["All", "completed", "failed", "processing"])
        
        with col3:
            limit = st.selectbox("Records to show", [25, 50, 100, 200])
        
        # Filter exports
        filtered_exports = exports
        if export_type_filter != "All":
            filtered_exports = [e for e in filtered_exports if e['export_type'] == export_type_filter]
        
        if status_filter != "All":
            filtered_exports = [e for e in filtered_exports if e['status'] == status_filter]
        
        filtered_exports = filtered_exports[:limit]
        
        if not filtered_exports:
            st.info("No exports found for the selected criteria.")
            return
        
        # Display exports
        export_data = []
        for export in filtered_exports:
            export_data.append({
                'Export Time': export['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'Type': export['export_type'].replace('_', ' ').title(),
                'Collection': export['collection_name'],
                'Batch': export['batch_name'],
                'Records': f"{export['record_count']:,}" if export['record_count'] else "N/A",
                'File Size': f"{export['file_size'] / (1024*1024):.1f} MB" if export['file_size'] else "N/A",
                'Status': export['status'].title(),
                'File Path': export['file_path']
            })
        
        df = pd.DataFrame(export_data)
        
        # Style the DataFrame
        def style_export_type(val):
            if val == 'Zip All':
                return 'background-color: #d1ecf1; color: #0c5460'
            elif val == 'Filtered Csv':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Raw Csv':
                return 'background-color: #fff3cd; color: #856404'
            elif val == 'Excel':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        def style_status(val):
            if val == 'Completed':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Failed':
                return 'background-color: #f8d7da; color: #721c24'
            elif val == 'Processing':
                return 'background-color: #fff3cd; color: #856404'
            return ''
        
        styled_df = df.style.applymap(style_export_type, subset=['Type']).applymap(style_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Export Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_exports = len(filtered_exports)
            st.metric("Total Exports", total_exports)
        
        with col2:
            total_records = sum(export['record_count'] for export in filtered_exports if export['record_count'])
            st.metric("Total Records Exported", f"{total_records:,}")
        
        with col3:
            total_size = sum(export['file_size'] for export in filtered_exports if export['file_size'])
            st.metric("Total Size Exported", f"{total_size / (1024*1024):.1f} MB")
        
        with col4:
            completed_exports = len([e for e in filtered_exports if e['status'] == 'completed'])
            success_rate = (completed_exports / total_exports * 100) if total_exports > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
    
    except Exception as e:
        st.error(f"Error loading export history: {e}")

def generate_export(batch_id, export_format, include_duplicates, encoding, delimiter):
    """Generate export for a specific batch"""
    try:
        # Get records
        records = db_manager.get_records_by_batch(batch_id, include_duplicates=include_duplicates)
        
        if not records:
            st.warning("No records found for this batch.")
            return
        
        # Get batch info
        batches = db_manager.get_batches_by_collection(st.session_state.get('selected_collection', ''))
        batch = next((b for b in batches if b['id'] == batch_id), None)
        
        if not batch:
            st.error("Batch not found.")
            return
        
        # Create export
        if export_format == "ZIP (All Files)":
            create_zip_export(batch, records, include_duplicates, encoding, delimiter)
        else:
            create_single_file_export(batch, records, export_format, include_duplicates, encoding, delimiter)
    
    except Exception as e:
        st.error(f"Error generating export: {e}")

def generate_custom_export(collection_ids, export_format, group_by, include_metadata, encoding, delimiter, selected_fields, start_date, end_date):
    """Generate custom export for multiple collections"""
    try:
        all_records = []
        
        # Collect records from all selected collections
        for collection_id in collection_ids:
            batches = db_manager.get_batches_by_collection(collection_id)
            for batch in batches:
                # Apply date filter if specified
                if start_date and end_date:
                    if batch['created_at'].date() < start_date or batch['created_at'].date() > end_date:
                        continue
                
                records = db_manager.get_records_by_batch(batch['id'], include_duplicates=False)
                for record in records:
                    record['collection_id'] = collection_id
                    record['batch_id'] = batch['id']
                    record['batch_name'] = batch['batch_name']
                
                all_records.extend(records)
        
        if not all_records:
            st.warning("No records found for the selected criteria.")
            return
        
        # Filter fields
        if selected_fields:
            all_records = [{k: v for k, v in record.items() if k in selected_fields} for record in all_records]
        
        # Create export based on grouping
        if group_by == "Collection":
            create_grouped_export_by_collection(all_records, export_format, encoding, delimiter)
        elif group_by == "Batch":
            create_grouped_export_by_batch(all_records, export_format, encoding, delimiter)
        else:
            create_single_file_export_custom(all_records, export_format, encoding, delimiter)
    
    except Exception as e:
        st.error(f"Error generating custom export: {e}")

def create_zip_export(batch, records, include_duplicates, encoding, delimiter):
    """Create ZIP export with multiple files"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{batch['batch_name']}_export.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Create main CSV
            df = pd.DataFrame(records)
            csv_path = os.path.join(temp_dir, f"{batch['batch_name']}_records.csv")
            df.to_csv(csv_path, index=False, encoding=encoding, sep=delimiter)
            zipf.write(csv_path, f"{batch['batch_name']}_records.csv")
            
            # Create filtered CSV (remove duplicates)
            if include_duplicates:
                filtered_df = df[~df.get('is_duplicate', False)]
                filtered_csv_path = os.path.join(temp_dir, f"{batch['batch_name']}_filtered.csv")
                filtered_df.to_csv(filtered_csv_path, index=False, encoding=encoding, sep=delimiter)
                zipf.write(filtered_csv_path, f"{batch['batch_name']}_filtered.csv")
            
            # Create summary
            summary_data = {
                'Total Records': len(df),
                'Filtered Records': len(df[~df.get('is_duplicate', False)]),
                'Duplicates': len(df[df.get('is_duplicate', False)]),
                'Export Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Batch Name': batch['batch_name'],
                'Collection': batch.get('collection_name', 'Unknown')
            }
            summary_df = pd.DataFrame([summary_data])
            summary_csv_path = os.path.join(temp_dir, "summary.csv")
            summary_df.to_csv(summary_csv_path, index=False, encoding=encoding, sep=delimiter)
            zipf.write(summary_csv_path, "summary.csv")
        
        # Download
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📦 Download ZIP Export",
                data=f.read(),
                file_name=f"{batch['batch_name']}_export.zip",
                mime="application/zip"
            )
        
        st.success("ZIP export created successfully!")
    
    except Exception as e:
        st.error(f"Error creating ZIP export: {e}")

def create_single_file_export(batch, records, export_format, include_duplicates, encoding, delimiter):
    """Create single file export"""
    try:
        df = pd.DataFrame(records)
        
        # Remove duplicates if not including them
        if not include_duplicates:
            df = df[~df.get('is_duplicate', False)]
        
        # Remove duplicate column for cleaner export
        if 'is_duplicate' in df.columns:
            df = df.drop('is_duplicate', axis=1)
        
        if export_format == "CSV":
            csv_data = df.to_csv(index=False, encoding=encoding, sep=delimiter)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"{batch['batch_name']}_export.csv",
                mime="text/csv"
            )
        elif export_format == "Excel":
            # For Excel, we need to create a temporary file
            temp_dir = tempfile.mkdtemp()
            excel_path = os.path.join(temp_dir, f"{batch['batch_name']}_export.xlsx")
            df.to_excel(excel_path, index=False)
            
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📊 Download Excel",
                    data=f.read(),
                    file_name=f"{batch['batch_name']}_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        st.success(f"{export_format} export created successfully!")
    
    except Exception as e:
        st.error(f"Error creating {export_format} export: {e}")

def create_single_file_export_custom(records, export_format, encoding, delimiter):
    """Create single file export for custom export"""
    try:
        df = pd.DataFrame(records)
        
        if export_format == "CSV":
            csv_data = df.to_csv(index=False, encoding=encoding, sep=delimiter)
            st.download_button(
                label="📄 Download Custom CSV",
                data=csv_data,
                file_name=f"custom_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        elif export_format == "Excel":
            temp_dir = tempfile.mkdtemp()
            excel_path = os.path.join(temp_dir, f"custom_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            df.to_excel(excel_path, index=False)
            
            with open(excel_path, "rb") as f:
                st.download_button(
                    label="📊 Download Custom Excel",
                    data=f.read(),
                    file_name=f"custom_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        st.success(f"Custom {export_format} export created successfully!")
    
    except Exception as e:
        st.error(f"Error creating custom export: {e}")

def create_grouped_export_by_collection(records, export_format, encoding, delimiter):
    """Create grouped export by collection"""
    try:
        # Group records by collection
        collections = {}
        for record in records:
            collection_id = record.get('collection_id', 'unknown')
            if collection_id not in collections:
                collections[collection_id] = []
            collections[collection_id].append(record)
        
        # Create ZIP with separate files for each collection
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "collections_export.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for collection_id, collection_records in collections.items():
                df = pd.DataFrame(collection_records)
                csv_path = os.path.join(temp_dir, f"collection_{collection_id}.csv")
                df.to_csv(csv_path, index=False, encoding=encoding, sep=delimiter)
                zipf.write(csv_path, f"collection_{collection_id}.csv")
        
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📦 Download Collections Export",
                data=f.read(),
                file_name=f"collections_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
        
        st.success("Collections export created successfully!")
    
    except Exception as e:
        st.error(f"Error creating collections export: {e}")

def create_grouped_export_by_batch(records, export_format, encoding, delimiter):
    """Create grouped export by batch"""
    try:
        # Group records by batch
        batches = {}
        for record in records:
            batch_id = record.get('batch_id', 'unknown')
            if batch_id not in batches:
                batches[batch_id] = []
            batches[batch_id].append(record)
        
        # Create ZIP with separate files for each batch
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "batches_export.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for batch_id, batch_records in batches.items():
                df = pd.DataFrame(batch_records)
                batch_name = batch_records[0].get('batch_name', f'batch_{batch_id}')
                csv_path = os.path.join(temp_dir, f"{batch_name}.csv")
                df.to_csv(csv_path, index=False, encoding=encoding, sep=delimiter)
                zipf.write(csv_path, f"{batch_name}.csv")
        
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📦 Download Batches Export",
                data=f.read(),
                file_name=f"batches_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
        
        st.success("Batches export created successfully!")
    
    except Exception as e:
        st.error(f"Error creating batches export: {e}")
