"""
History page - View processing logs and audit trail
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import db_manager

def render():
    """Render the history page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📊 Processing History")
    st.markdown("Monitor processing logs, audit trail, and system activity")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Processing Logs", "Export History", "System Activity"])
    
    with tab1:
        render_processing_logs()
    
    with tab2:
        render_export_history()
    
    with tab3:
        render_system_activity()

def render_processing_logs():
    """Render processing logs view"""
    st.subheader("📋 Processing Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
    
    with col2:
        days_back = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"])
    
    with col3:
        limit = st.selectbox("Records to show", [50, 100, 200, 500])
    
    try:
        # Get logs
        logs = db_manager.get_processing_logs(limit=limit)
        
        # Filter by log level
        if log_level != "All":
            logs = [log for log in logs if log['log_level'] == log_level]
        
        # Filter by time range
        if days_back != "All time":
            if days_back == "Last 24 hours":
                cutoff = datetime.now() - timedelta(hours=24)
            elif days_back == "Last 7 days":
                cutoff = datetime.now() - timedelta(days=7)
            elif days_back == "Last 30 days":
                cutoff = datetime.now() - timedelta(days=30)
            
            logs = [log for log in logs if log['created_at'] >= cutoff]
        
        if not logs:
            st.info("No logs found for the selected criteria.")
            return
        
        # Display logs
        log_data = []
        for log in logs:
            log_data.append({
                'Time': log['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'Level': log['log_level'],
                'Collection': log.get('collection_name', 'N/A'),
                'Batch': log.get('batch_name', 'N/A'),
                'File': log.get('file_name', 'N/A'),
                'Message': log['message'],
                'Details': str(log.get('details', ''))[:100] + "..." if log.get('details') and len(str(log.get('details'))) > 100 else str(log.get('details', ''))
            })
        
        df = pd.DataFrame(log_data)
        
        # Style the DataFrame
        def style_log_level(val):
            if val == 'ERROR':
                return 'background-color: #f8d7da; color: #721c24'
            elif val == 'WARNING':
                return 'background-color: #fff3cd; color: #856404'
            elif val == 'INFO':
                return 'background-color: #d1ecf1; color: #0c5460'
            elif val == 'DEBUG':
                return 'background-color: #e2e3e5; color: #383d41'
            return ''
        
        styled_df = df.style.applymap(style_log_level, subset=['Level'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Log Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            error_count = len([log for log in logs if log['log_level'] == 'ERROR'])
            st.metric("Errors", error_count)
        
        with col2:
            warning_count = len([log for log in logs if log['log_level'] == 'WARNING'])
            st.metric("Warnings", warning_count)
        
        with col3:
            info_count = len([log for log in logs if log['log_level'] == 'INFO'])
            st.metric("Info Messages", info_count)
        
        with col4:
            total_logs = len(logs)
            st.metric("Total Logs", total_logs)
    
    except Exception as e:
        st.error(f"Error loading processing logs: {e}")

def render_export_history():
    """Render export history view"""
    st.subheader("💾 Export History")
    
    try:
        # Get export history
        exports = db_manager.get_export_history(limit=100)
        
        if not exports:
            st.info("No exports found.")
            return
        
        # Display exports
        export_data = []
        for export in exports:
            export_data.append({
                'Export Time': export['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'Type': export['export_type'],
                'Collection': export['collection_name'],
                'Batch': export['batch_name'],
                'Records': export['record_count'],
                'File Size': f"{export['file_size'] / (1024*1024):.1f} MB" if export['file_size'] else "N/A",
                'Status': export['status'],
                'File Path': export['file_path']
            })
        
        df = pd.DataFrame(export_data)
        
        # Style the DataFrame
        def style_export_type(val):
            if val == 'zip_all':
                return 'background-color: #d1ecf1; color: #0c5460'
            elif val == 'filtered_csv':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'raw_csv':
                return 'background-color: #fff3cd; color: #856404'
            elif val == 'excel':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        styled_df = df.style.applymap(style_export_type, subset=['Type'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Summary statistics
        st.subheader("📊 Export Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_exports = len(exports)
            st.metric("Total Exports", total_exports)
        
        with col2:
            total_records = sum(export['record_count'] for export in exports if export['record_count'])
            st.metric("Total Records Exported", f"{total_records:,}")
        
        with col3:
            total_size = sum(export['file_size'] for export in exports if export['file_size'])
            st.metric("Total Size Exported", f"{total_size / (1024*1024):.1f} MB")
        
        with col4:
            recent_exports = len([e for e in exports if e['created_at'].date() == datetime.now().date()])
            st.metric("Exports Today", recent_exports)
    
    except Exception as e:
        st.error(f"Error loading export history: {e}")

def render_system_activity():
    """Render system activity view"""
    st.subheader("⚡ System Activity")
    
    try:
        # Get collections for activity overview
        collections = db_manager.get_collections(limit=50)
        
        if not collections:
            st.info("No collections found.")
            return
        
        # Activity overview
        st.subheader("📈 Activity Overview")
        
        # Recent collections
        recent_collections = [c for c in collections if c['created_date'].date() >= (datetime.now() - timedelta(days=7)).date()]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Collections Created (7 days)", len(recent_collections))
        
        with col2:
            active_collections = len([c for c in collections if c['status'] == 'active'])
            st.metric("Active Collections", active_collections)
        
        with col3:
            total_records = sum(c.get('total_records', 0) for c in collections)
            st.metric("Total Records Processed", f"{total_records:,}")
        
        with col4:
            archived_collections = len([c for c in collections if c['status'] == 'archived'])
            st.metric("Archived Collections", archived_collections)
        
        # Recent activity timeline
        st.subheader("📅 Recent Activity Timeline")
        
        # Get recent batches
        recent_batches = []
        for collection in collections[:10]:  # Check last 10 collections
            batches = db_manager.get_batches_by_collection(collection['id'])
            for batch in batches:
                recent_batches.append({
                    'Collection': collection['collection_name'],
                    'Batch': batch['batch_name'],
                    'Status': batch['status'],
                    'Records': batch.get('total_records', 0),
                    'Created': batch['created_at'],
                    'Completed': batch.get('processing_completed_at')
                })
        
        if recent_batches:
            # Sort by creation date
            recent_batches.sort(key=lambda x: x['Created'], reverse=True)
            
            # Display timeline
            for batch in recent_batches[:20]:  # Show last 20 batches
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{batch['Collection']}** - {batch['Batch']}")
                        st.caption(f"Created: {batch['Created'].strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        status_color = {
                            'completed': '🟢',
                            'processing': '🟡',
                            'failed': '🔴',
                            'pending': '⚪'
                        }.get(batch['Status'], '❓')
                        st.markdown(f"{status_color} {batch['Status'].title()}")
                    
                    with col3:
                        st.metric("Records", f"{batch['Records']:,}")
                    
                    with col4:
                        if batch['Completed']:
                            st.caption(f"Completed: {batch['Completed'].strftime('%H:%M')}")
                        else:
                            st.caption("In Progress")
                    
                    st.markdown("---")
        else:
            st.info("No recent batch activity found.")
        
        # System health indicators
        st.subheader("🏥 System Health")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Check for recent errors
            try:
                recent_logs = db_manager.get_processing_logs(limit=100)
                recent_errors = [log for log in recent_logs if log['log_level'] == 'ERROR' and log['created_at'].date() == datetime.now().date()]
                error_count = len(recent_errors)
                
                if error_count == 0:
                    st.success("✅ No errors today")
                elif error_count < 5:
                    st.warning(f"⚠️ {error_count} errors today")
                else:
                    st.error(f"❌ {error_count} errors today")
            except:
                st.error("❌ Unable to check error status")
        
        with col2:
            # Check database connectivity
            try:
                test_collections = db_manager.get_collections(limit=1)
                st.success("✅ Database connected")
            except:
                st.error("❌ Database connection issue")
        
        with col3:
            # Check processing status
            try:
                processing_batches = []
                for collection in collections:
                    batches = db_manager.get_batches_by_collection(collection['id'])
                    processing_batches.extend([b for b in batches if b['status'] == 'processing'])
                
                if not processing_batches:
                    st.success("✅ No active processing")
                else:
                    st.info(f"🔄 {len(processing_batches)} batches processing")
            except:
                st.warning("⚠️ Unable to check processing status")
    
    except Exception as e:
        st.error(f"Error loading system activity: {e}")
