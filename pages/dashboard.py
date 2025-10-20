"""
Dashboard page - Main overview and quick actions
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import db_manager

def render():
    """Render the dashboard page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🏠 Dashboard")
    st.markdown("Welcome to the PDF to CSV Pipeline - Your data processing command center")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # KPIs Section
    st.subheader("📊 Key Performance Indicators")
    
    try:
        # Get collections data
        collections = db_manager.get_collections(limit=100)
        active_collections = [c for c in collections if c['status'] == 'active']
        archived_collections = [c for c in collections if c['status'] == 'archived']
        
        # Calculate metrics
        total_collections = len(collections)
        total_records = sum(c.get('total_records', 0) for c in collections)
        recent_collections = len([c for c in collections if c['created_date'].date() >= (datetime.now() - timedelta(days=7)).date()])
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Active Collections", 
                len(active_collections),
                delta=f"+{recent_collections} this week"
            )
        
        with col2:
            st.metric(
                "Total Records", 
                f"{total_records:,}",
                delta=f"{len(archived_collections)} archived"
            )
        
        with col3:
            # Get recent batches
            recent_batches = []
            for collection in collections[:5]:  # Check last 5 collections
                batches = db_manager.get_batches_by_collection(collection['id'])
                recent_batches.extend(batches)
            
            processing_batches = len([b for b in recent_batches if b['status'] == 'processing'])
            st.metric(
                "Processing Batches", 
                processing_batches,
                delta=f"{len(recent_batches)} total batches"
            )
        
        with col4:
            # Calculate duplicates found
            total_duplicates = sum(b.get('duplicates_found', 0) for b in recent_batches)
            st.metric(
                "Duplicates Found", 
                total_duplicates,
                delta="across all batches"
            )
    
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        return
    
    st.markdown("---")
    
    # Recent Collections Section
    st.subheader("📁 Recent Collections")
    
    if collections:
        # Create a DataFrame for display
        df_data = []
        for collection in collections[:10]:  # Show last 10
            df_data.append({
                'Collection Name': collection['collection_name'],
                'Client': collection['client_name'],
                'Status': collection['status'],
                'Records': collection.get('total_records', 0),
                'Created': collection['created_date'].strftime('%Y-%m-%d %H:%M'),
                'Last Updated': collection['last_updated_date'].strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(df_data)
        
        # Style the DataFrame
        def style_status(val):
            if val == 'active':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'archived':
                return 'background-color: #e2e3e5; color: #383d41'
            elif val == 'processing':
                return 'background-color: #fff3cd; color: #856404'
            return ''
        
        styled_df = df.style.applymap(style_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Create New Collection", use_container_width=True):
                st.session_state.current_page = "Collections"
                st.rerun()
        
        with col2:
            if st.button("⚡ Start Processing", use_container_width=True):
                st.session_state.current_page = "Processing"
                st.rerun()
        
        with col3:
            if st.button("📊 View All Collections", use_container_width=True):
                st.session_state.current_page = "Collections"
                st.rerun()
    
    else:
        st.info("No collections found. Create your first collection to get started!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Create First Collection", use_container_width=True):
                st.session_state.current_page = "Collections"
                st.rerun()
        
        with col2:
            if st.button("⚡ Start Processing", use_container_width=True):
                st.session_state.current_page = "Processing"
                st.rerun()
    
    st.markdown("---")
    
    # Recent Activity Section
    st.subheader("📈 Recent Activity")
    
    try:
        # Get recent processing logs
        logs = db_manager.get_processing_logs(limit=20)
        
        if logs:
            # Group logs by batch
            activity_data = []
            for log in logs[:10]:
                activity_data.append({
                    'Time': log['created_at'].strftime('%H:%M:%S'),
                    'Level': log['log_level'],
                    'Message': log['message'][:50] + "..." if len(log['message']) > 50 else log['message'],
                    'Collection': log.get('collection_name', 'N/A'),
                    'Batch': log.get('batch_name', 'N/A')
                })
            
            activity_df = pd.DataFrame(activity_data)
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No recent activity found.")
    
    except Exception as e:
        st.warning(f"Could not load recent activity: {e}")
    
    # Quick Tips Section
    st.markdown("---")
    st.subheader("💡 Quick Tips")
    
    tips = [
        "💡 Use collections to organize your PDFs by client or project",
        "⚡ Process PDFs in batches of 25 for optimal performance",
        "🔍 Check the History page to monitor processing progress",
        "📊 Use the Exports page to download your processed data",
        "⚙️ Configure settings for your specific requirements"
    ]
    
    for tip in tips:
        st.markdown(tip)
