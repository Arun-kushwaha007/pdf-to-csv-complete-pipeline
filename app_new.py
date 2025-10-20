"""
PDF to CSV Pipeline - Enhanced UI with Collections Management
Main application with redesigned interface for better workflow management
"""

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
from typing import List, Dict, Optional
import json

# Import modules
from working_document_processor import WorkingDocumentProcessor
from database import db_manager
import pages.dashboard as dashboard_page
import pages.collections as collections_page
import pages.processing as processing_page
import pages.history as history_page
import pages.exports as exports_page
import pages.settings as settings_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PDF to CSV Pipeline",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-active { background-color: #d4edda; color: #155724; }
    .status-processing { background-color: #fff3cd; color: #856404; }
    .status-completed { background-color: #d1ecf1; color: #0c5460; }
    .status-failed { background-color: #f8d7da; color: #721c24; }
    .status-archived { background-color: #e2e3e5; color: #383d41; }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    .collection-card {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
        transition: box-shadow 0.2s;
    }
    
    .collection-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .duplicate-row {
        background-color: #fff3cd !important;
    }
    
    .invalid-row {
        background-color: #f8d7da !important;
    }
    
    .valid-row {
        background-color: #d4edda !important;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedProcessor:
    def __init__(self):
        self.project_id = os.getenv('PROJECT_ID', 'pdf2csv-converter-tool')
        self.location = os.getenv('LOCATION', 'us')
        self.processor_id = os.getenv('CUSTOM_PROCESSOR_ID', 'e3a0679d2b58c372')
        self.processor = WorkingDocumentProcessor(self.project_id, self.location)
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_single_pdf(self, pdf_path: str, batch_id: str, file_id: str) -> dict:
        """Process a single PDF and store results in database"""
        try:
            start_time = time.time()
            result = self.processor.process_document(pdf_path, self.processor_id)
            processing_time = time.time() - start_time
            
            raw_records = result.get('raw_records', [])
            filtered_records = result.get('filtered_records', [])
            
            # Update file status
            db_manager.update_file_status(
                file_id, 
                'completed' if raw_records or filtered_records else 'failed',
                processing_time_seconds=processing_time
            )
            
            # Store records in database
            if raw_records:
                db_manager.create_records(batch_id, file_id, raw_records)
            
            # Log processing event
            db_manager.log_processing_event(
                batch_id, file_id, 'INFO',
                f"Processed {len(raw_records)} raw records, {len(filtered_records)} filtered records",
                {'processing_time': processing_time, 'raw_count': len(raw_records), 'filtered_count': len(filtered_records)}
            )
            
            return {
                'status': 'success',
                'file_id': file_id,
                'raw_records': raw_records,
                'filtered_records': filtered_records,
                'raw_count': len(raw_records),
                'filtered_count': len(filtered_records),
                'time': processing_time
            }
            
        except Exception as e:
            # Update file status to failed
            db_manager.update_file_status(file_id, 'failed', error_message=str(e))
            
            # Log error
            db_manager.log_processing_event(
                batch_id, file_id, 'ERROR',
                f"Processing failed: {str(e)}",
                {'error': str(e)}
            )
            
            return {
                'status': 'error',
                'file_id': file_id,
                'error': str(e),
                'raw_records': [],
                'filtered_records': [],
                'raw_count': 0,
                'filtered_count': 0,
                'time': 0
            }
    
    def process_batch(self, uploaded_files, batch_id: str, max_workers: int = 3) -> List[dict]:
        """Process a batch of PDFs and store in database"""
        results = []
        file_ids = []
        
        # Create file records in database
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            file_id = db_manager.create_file(
                batch_id, 
                uploaded_file.name, 
                temp_path, 
                uploaded_file.size
            )
            file_ids.append((file_id, temp_path))
        
        # Update batch with total files
        db_manager.update_batch_status(batch_id, 'processing', total_files=len(uploaded_files))
        
        # Process files
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_pdf, path, batch_id, file_id): (file_id, path)
                for file_id, path in file_ids
            }
            
            completed = 0
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
                completed += 1
                
                # Update progress
                db_manager.update_batch_status(
                    batch_id, 
                    'processing', 
                    processed_files=completed
                )
        
        # Calculate totals and update batch
        total_raw = sum(r.get('raw_count', 0) for r in results if r['status'] == 'success')
        total_filtered = sum(r.get('filtered_count', 0) for r in results if r['status'] == 'success')
        successful_files = len([r for r in results if r['status'] == 'success'])
        
        # Detect duplicates
        duplicates_found = db_manager.detect_duplicates(batch_id)
        
        # Update batch status
        db_manager.update_batch_status(
            batch_id,
            'completed',
            total_records=total_raw,
            filtered_records=total_filtered,
            duplicates_found=duplicates_found,
            processing_completed_at=datetime.now()
        )
        
        return results

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = None
    
    if 'selected_batch' not in st.session_state:
        st.session_state.selected_batch = None
    
    if 'processor' not in st.session_state:
        try:
            st.session_state.processor = EnhancedProcessor()
        except Exception as e:
            st.error(f"Failed to initialize processor: {e}")
            st.stop()

def render_sidebar():
    """Render the sidebar navigation"""
    st.sidebar.title("📄 PDF to CSV Pipeline")
    
    # Navigation menu
    pages = {
        "Dashboard": "🏠",
        "Collections": "📁",
        "Processing": "⚡",
        "History": "📊",
        "Exports": "💾",
        "Settings": "⚙️"
    }
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")
    
    for page_name, icon in pages.items():
        if st.sidebar.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
            st.session_state.current_page = page_name
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Quick stats
    try:
        collections = db_manager.get_collections(limit=5)
        active_collections = len([c for c in collections if c['status'] == 'active'])
        
        st.sidebar.markdown("### Quick Stats")
        st.sidebar.metric("Active Collections", active_collections)
        
        if collections:
            latest_collection = collections[0]
            st.sidebar.metric("Latest Collection", latest_collection['collection_name'][:20] + "...")
    except Exception as e:
        st.sidebar.error("Database connection error")

def render_main_content():
    """Render the main content based on current page"""
    page = st.session_state.current_page
    
    if page == "Dashboard":
        dashboard_page.render()
    elif page == "Collections":
        collections_page.render()
    elif page == "Processing":
        processing_page.render()
    elif page == "History":
        history_page.render()
    elif page == "Exports":
        exports_page.render()
    elif page == "Settings":
        settings_page.render()

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()
