"""
Collections page - Manage collections and batches
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import db_manager

def render():
    """Render the collections page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📁 Collections Management")
    st.markdown("Organize and manage your PDF processing collections")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Active Collections", "Archived Collections", "Create New Collection"])
    
    with tab1:
        render_active_collections()
    
    with tab2:
        render_archived_collections()
    
    with tab3:
        render_create_collection()

def render_active_collections():
    """Render active collections view"""
    st.subheader("🟢 Active Collections")
    
    try:
        collections = db_manager.get_collections(status='active', limit=50)
        
        if not collections:
            st.info("No active collections found.")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            client_filter = st.selectbox(
                "Filter by Client",
                ["All"] + list(set(c['client_name'] for c in collections))
            )
        
        with col2:
            search_term = st.text_input("Search collections", placeholder="Enter collection name...")
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Created Date", "Last Updated", "Records Count", "Collection Name"])
        
        # Filter collections
        filtered_collections = collections
        if client_filter != "All":
            filtered_collections = [c for c in filtered_collections if c['client_name'] == client_filter]
        
        if search_term:
            filtered_collections = [c for c in filtered_collections if search_term.lower() in c['collection_name'].lower()]
        
        # Sort collections
        if sort_by == "Created Date":
            filtered_collections.sort(key=lambda x: x['created_date'], reverse=True)
        elif sort_by == "Last Updated":
            filtered_collections.sort(key=lambda x: x['last_updated_date'], reverse=True)
        elif sort_by == "Records Count":
            filtered_collections.sort(key=lambda x: x.get('total_records', 0), reverse=True)
        elif sort_by == "Collection Name":
            filtered_collections.sort(key=lambda x: x['collection_name'])
        
        # Display collections
        for collection in filtered_collections:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{collection['collection_name']}**")
                    st.caption(f"Client: {collection['client_name']}")
                    if collection.get('notes'):
                        st.caption(f"Notes: {collection['notes']}")
                
                with col2:
                    st.metric("Records", f"{collection.get('total_records', 0):,}")
                    st.caption(f"Created: {collection['created_date'].strftime('%Y-%m-%d')}")
                
                with col3:
                    if st.button("View", key=f"view_{collection['id']}"):
                        st.session_state.selected_collection = collection['id']
                        st.session_state.current_page = "Collections"
                        st.rerun()
                
                with col4:
                    if st.button("Archive", key=f"archive_{collection['id']}"):
                        db_manager.archive_collection(collection['id'])
                        st.success("Collection archived successfully!")
                        st.rerun()
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"Error loading collections: {e}")

def render_archived_collections():
    """Render archived collections view"""
    st.subheader("📦 Archived Collections")
    
    try:
        collections = db_manager.get_collections(status='archived', limit=50)
        
        if not collections:
            st.info("No archived collections found.")
            return
        
        # Display archived collections
        for collection in collections:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{collection['collection_name']}**")
                    st.caption(f"Client: {collection['client_name']}")
                    st.caption(f"Archived: {collection['last_updated_date'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.metric("Records", f"{collection.get('total_records', 0):,}")
                    st.caption(f"Created: {collection['created_date'].strftime('%Y-%m-%d')}")
                
                with col3:
                    if st.button("View", key=f"view_archived_{collection['id']}"):
                        st.session_state.selected_collection = collection['id']
                        st.session_state.current_page = "Collections"
                        st.rerun()
                
                with col4:
                    if st.button("Unarchive", key=f"unarchive_{collection['id']}"):
                        db_manager.unarchive_collection(collection['id'])
                        st.success("Collection unarchived successfully!")
                        st.rerun()
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"Error loading archived collections: {e}")

def render_create_collection():
    """Render create collection form"""
    st.subheader("➕ Create New Collection")
    
    with st.form("create_collection_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            collection_name = st.text_input("Collection Name *", placeholder="e.g., Weekly Data - Week 1")
            client_name = st.text_input("Client Name *", placeholder="e.g., ABC Company")
        
        with col2:
            batch_id = st.text_input("Batch ID", placeholder="e.g., BATCH-001")
            notes = st.text_area("Notes", placeholder="Optional notes about this collection...")
        
        submitted = st.form_submit_button("Create Collection", use_container_width=True)
        
        if submitted:
            if not collection_name or not client_name:
                st.error("Please fill in all required fields.")
            else:
                try:
                    collection_id = db_manager.create_collection(
                        collection_name=collection_name,
                        client_name=client_name,
                        notes=notes if notes else None,
                        batch_id=batch_id if batch_id else None
                    )
                    st.success(f"Collection '{collection_name}' created successfully!")
                    st.info(f"Collection ID: {collection_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating collection: {e}")

def render_collection_detail(collection_id: str):
    """Render detailed view of a specific collection"""
    try:
        collection = db_manager.get_collection_by_id(collection_id)
        if not collection:
            st.error("Collection not found.")
            return
        
        st.subheader(f"📁 {collection['collection_name']}")
        
        # Collection info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Client", collection['client_name'])
            st.metric("Status", collection['status'].title())
        with col2:
            st.metric("Total Records", f"{collection.get('total_records', 0):,}")
            st.metric("Created", collection['created_date'].strftime('%Y-%m-%d'))
        with col3:
            st.metric("Last Updated", collection['last_updated_date'].strftime('%Y-%m-%d %H:%M'))
            if collection.get('batch_id'):
                st.metric("Batch ID", collection['batch_id'])
        
        if collection.get('notes'):
            st.info(f"Notes: {collection['notes']}")
        
        st.markdown("---")
        
        # Batches for this collection
        st.subheader("📦 Batches")
        batches = db_manager.get_batches_by_collection(collection_id)
        
        if batches:
            batch_data = []
            for batch in batches:
                batch_data.append({
                    'Batch Name': batch['batch_name'],
                    'Status': batch['status'],
                    'Files': f"{batch['processed_files']}/{batch['total_files']}",
                    'Records': batch.get('total_records', 0),
                    'Filtered': batch.get('filtered_records', 0),
                    'Duplicates': batch.get('duplicates_found', 0),
                    'Created': batch['created_at'].strftime('%Y-%m-%d %H:%M')
                })
            
            df = pd.DataFrame(batch_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No batches found for this collection.")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Create New Batch"):
                st.session_state.selected_collection = collection_id
                st.session_state.current_page = "Processing"
                st.rerun()
        
        with col2:
            if st.button("📊 View Records"):
                # This would show records in a detailed view
                st.info("Records view coming soon...")
        
        with col3:
            if collection['status'] == 'active':
                if st.button("📦 Archive Collection"):
                    db_manager.archive_collection(collection_id)
                    st.success("Collection archived!")
                    st.rerun()
            else:
                if st.button("🔄 Unarchive Collection"):
                    db_manager.unarchive_collection(collection_id)
                    st.success("Collection unarchived!")
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error loading collection details: {e}")
