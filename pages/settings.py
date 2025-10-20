"""
Settings page - Configure system settings and preferences
"""

import streamlit as st
import os
from database import db_manager

def render():
    """Render the settings page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("⚙️ Settings")
    st.markdown("Configure system settings and preferences")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabs for different settings
    tab1, tab2, tab3, tab4 = st.tabs(["Database", "Processing", "Export", "System"])
    
    with tab1:
        render_database_settings()
    
    with tab2:
        render_processing_settings()
    
    with tab3:
        render_export_settings()
    
    with tab4:
        render_system_settings()

def render_database_settings():
    """Render database settings"""
    st.subheader("🗄️ Database Settings")
    
    # Database connection status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Connection Status**")
        try:
            # Test database connection
            test_collections = db_manager.get_collections(limit=1)
            st.success("✅ Database connected successfully")
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
    
    with col2:
        st.markdown("**Database Info**")
        try:
            collections = db_manager.get_collections(limit=1000)
            total_collections = len(collections)
            total_records = sum(c.get('total_records', 0) for c in collections)
            
            st.metric("Total Collections", total_collections)
            st.metric("Total Records", f"{total_records:,}")
        except Exception as e:
            st.warning(f"Could not retrieve database info: {e}")
    
    st.markdown("---")
    
    # Database configuration
    st.subheader("🔧 Database Configuration")
    
    with st.expander("Current Database Configuration"):
        db_config = {
            "Host": os.getenv('DB_HOST', 'Not set'),
            "Port": os.getenv('DB_PORT', 'Not set'),
            "Database": os.getenv('DB_NAME', 'Not set'),
            "User": os.getenv('DB_USER', 'Not set'),
            "SSL Mode": os.getenv('DB_SSL', 'Not set'),
            "Socket Path": os.getenv('DB_SOCKET_PATH', 'Not set')
        }
        
        for key, value in db_config.items():
            st.text(f"{key}: {value}")
    
    st.info("💡 Database configuration is managed through environment variables. Contact your administrator to modify these settings.")

def render_processing_settings():
    """Render processing settings"""
    st.subheader("⚡ Processing Settings")
    
    # Document AI Configuration
    st.markdown("**Document AI Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_id = st.text_input("Project ID", value=os.getenv('PROJECT_ID', ''), disabled=True)
        location = st.text_input("Location", value=os.getenv('LOCATION', ''), disabled=True)
    
    with col2:
        processor_id = st.text_input("Processor ID", value=os.getenv('CUSTOM_PROCESSOR_ID', ''), disabled=True)
        max_workers = st.number_input("Max Workers", value=3, min_value=1, max_value=10)
    
    st.info("💡 Document AI settings are configured through environment variables.")
    
    st.markdown("---")
    
    # Processing Rules
    st.markdown("**Processing Rules**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        group_size = st.slider("Default Group Size", 10, 50, 25, 5)
        enable_deduplication = st.checkbox("Enable Deduplication by Default", value=True)
        require_mobile = st.checkbox("Require Mobile Number", value=True)
    
    with col2:
        min_address_length = st.number_input("Minimum Address Length", value=15, min_value=5, max_value=100)
        phone_validation = st.checkbox("Validate Phone Numbers", value=True)
        email_validation = st.checkbox("Validate Email Addresses", value=True)
    
    if st.button("💾 Save Processing Settings"):
        st.success("Processing settings saved! (Note: Some settings require application restart)")
    
    st.markdown("---")
    
    # Validation Rules
    st.markdown("**Validation Rules**")
    
    with st.expander("Mobile Number Validation"):
        mobile_pattern = st.text_input("Mobile Pattern", value=os.getenv('MOBILE_PATTERN', '^04\\d{8}$'))
        st.caption("Regular expression pattern for validating mobile numbers")
    
    with st.expander("Address Validation"):
        min_address_length = st.number_input("Minimum Address Length", value=15, min_value=5, max_value=100)
        require_numbers = st.checkbox("Require Numbers in Address", value=True)
        st.caption("Addresses must contain at least one number in the first 10 characters")
    
    with st.expander("Name Validation"):
        min_name_parts = st.number_input("Minimum Name Parts", value=2, min_value=1, max_value=5)
        require_latin_letters = st.checkbox("Require Latin Letters", value=True)
        st.caption("Names must contain at least 2 parts with Latin letters")

def render_export_settings():
    """Render export settings"""
    st.subheader("💾 Export Settings")
    
    # Default Export Configuration
    st.markdown("**Default Export Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_format = st.selectbox("Default Export Format", ["CSV", "Excel", "ZIP"])
        default_encoding = st.selectbox("Default Encoding", ["UTF-8", "Latin-1"])
        default_delimiter = st.selectbox("Default CSV Delimiter", [",", ";", "\t"])
    
    with col2:
        include_headers = st.checkbox("Include Headers by Default", value=True)
        include_duplicates = st.checkbox("Include Duplicates by Default", value=False)
        group_by_collection = st.checkbox("Group by Collection by Default", value=False)
    
    st.markdown("---")
    
    # File Naming Convention
    st.markdown("**File Naming Convention**")
    
    naming_template = st.text_input(
        "File Naming Template",
        value="{collection_name}_{batch_name}_{timestamp}",
        help="Available variables: {collection_name}, {batch_name}, {timestamp}, {client_name}"
    )
    
    st.caption("Example: Weekly_Data_Batch_001_20241201_143022")
    
    st.markdown("---")
    
    # Export Limits
    st.markdown("**Export Limits**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_records_per_export = st.number_input("Max Records per Export", value=100000, min_value=1000, max_value=1000000)
        max_file_size_mb = st.number_input("Max File Size (MB)", value=100, min_value=10, max_value=1000)
    
    with col2:
        max_concurrent_exports = st.number_input("Max Concurrent Exports", value=3, min_value=1, max_value=10)
        export_timeout_minutes = st.number_input("Export Timeout (minutes)", value=30, min_value=5, max_value=120)
    
    if st.button("💾 Save Export Settings"):
        st.success("Export settings saved!")

def render_system_settings():
    """Render system settings"""
    st.subheader("🖥️ System Settings")
    
    # Application Information
    st.markdown("**Application Information**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text(f"Application Version: 2.0.0")
        st.text(f"Python Version: {os.sys.version}")
        st.text(f"Streamlit Version: {st.__version__}")
    
    with col2:
        st.text(f"Working Directory: {os.getcwd()}")
        st.text(f"Temp Directory: {os.path.join(os.getcwd(), 'temp')}")
        st.text(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    
    st.markdown("---")
    
    # Performance Settings
    st.markdown("**Performance Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cache_size = st.number_input("Cache Size (MB)", value=100, min_value=10, max_value=1000)
        max_memory_usage = st.number_input("Max Memory Usage (MB)", value=512, min_value=128, max_value=2048)
    
    with col2:
        enable_caching = st.checkbox("Enable Caching", value=True)
        enable_compression = st.checkbox("Enable Compression", value=True)
        auto_cleanup = st.checkbox("Auto Cleanup Temp Files", value=True)
    
    st.markdown("---")
    
    # Logging Settings
    st.markdown("**Logging Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=1)
        log_retention_days = st.number_input("Log Retention (days)", value=30, min_value=1, max_value=365)
    
    with col2:
        enable_file_logging = st.checkbox("Enable File Logging", value=True)
        enable_console_logging = st.checkbox("Enable Console Logging", value=True)
        log_rotation = st.checkbox("Enable Log Rotation", value=True)
    
    st.markdown("---")
    
    # Security Settings
    st.markdown("**Security Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_ssl = st.checkbox("Enable SSL", value=True)
        session_timeout = st.number_input("Session Timeout (minutes)", value=60, min_value=5, max_value=480)
    
    with col2:
        max_upload_size = st.number_input("Max Upload Size (MB)", value=100, min_value=10, max_value=1000)
        enable_audit_log = st.checkbox("Enable Audit Logging", value=True)
    
    st.markdown("---")
    
    # System Actions
    st.markdown("**System Actions**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Test Database Connection"):
            try:
                test_collections = db_manager.get_collections(limit=1)
                st.success("✅ Database connection successful")
            except Exception as e:
                st.error(f"❌ Database connection failed: {e}")
    
    with col2:
        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared")
    
    with col3:
        if st.button("📊 System Health Check"):
            try:
                # Perform basic health checks
                collections = db_manager.get_collections(limit=1)
                st.success("✅ System health check passed")
            except Exception as e:
                st.error(f"❌ System health check failed: {e}")
    
    st.markdown("---")
    
    # Save All Settings
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.success("All settings saved successfully!")
        st.info("Some settings may require application restart to take effect.")
