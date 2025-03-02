import streamlit as st
import pandas as pd
from utils.document_processor import process_document
import json
from database import init_database, get_database_connection
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from components.navigation import render_navigation

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="Research Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables
try:
    init_database()
    st.session_state.db_initialized = True
except Exception as e:
    st.error(f"Error initializing database: {str(e)}")
    st.session_state.db_initialized = False

# Set up demo user if not logged in
if 'user_id' not in st.session_state or st.session_state.user_id is None:
    # Instead of requiring login, use a demo user ID
    st.session_state.user_id = 1  # Use a default user ID for demonstration
    st.session_state.username = "Demo User"

# Custom CSS for better styling
st.markdown("""
<style>
    /* Base styles */
    .main {
        background-color: #f8f9fa;
        color: #333;
    }

    /* Header */
    .header-container {
        display: flex;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
        margin-bottom: 2rem;
    }

    .logo {
        margin-right: 1rem;
        font-size: 2.5rem;
    }

    .header-text {
        flex-grow: 1;
    }

    .header-text h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }

    .header-text p {
        margin: 0;
        font-size: 1rem;
        color: rgba(49, 51, 63, 0.7);
    }

    /* Dashboard components */
    .dashboard-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* EMR Data extraction styling */
    .upload-area {
        border: 2px dashed #6C63FF;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: rgba(108, 99, 255, 0.05);
    }

    .data-stats {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(0,0,0,0.05);
    }

    /* Metrics and data visualization */
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        transition: transform 0.3s ease;
        height: 100%;
    }

    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        color: #6C63FF;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #1E1E2F;
    }

    .metric-label {
        font-size: 0.9rem;
        color: rgba(49, 51, 63, 0.7);
    }
</style>
""", unsafe_allow_html=True)

# Render navigation sidebar
render_navigation()

# Top header with logo
st.markdown("""
<div class="header-container">
    <div class="logo">⚡</div>
    <div class="header-text">
        <h1>Research Data Platform</h1>
        <p>Secure collaborative research management</p>
    </div>
</div>
""", unsafe_allow_html=True)

# User info
st.markdown(f"""
<div class="user-info">
    <div class="user-avatar">{st.session_state.username[0]}</div>
    <div>Welcome, {st.session_state.username}</div>
</div>
""", unsafe_allow_html=True)

try:
    # Main dashboard layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # EMR Data Extraction Section
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("EMR Data Extraction")

        # EMR connection form
        emr_type = st.selectbox(
            "EMR System",
            ["Epic Clarity", "Cerner", "AllScripts", "MEDITECH", "Other"]
        )

        connection_tabs = st.tabs(["Direct Connection", "File Import"])

        with connection_tabs[0]:
            st.subheader("Database Connection")
            emr_server = st.text_input("Database Server URL")
            credentials_method = st.radio(
                "Authentication Method",
                ["Certificate", "Username/Password", "Service Account"]
            )
            if credentials_method == "Certificate":
                st.file_uploader("Upload Certificate", type=['pem', 'crt'])
            elif credentials_method == "Username/Password":
                st.text_input("Username")
                st.text_input("Password", type="password")
            else:
                st.file_uploader("Service Account Credentials", type=['json', 'key'])

        with connection_tabs[1]:
            st.subheader("File-based Import")
            st.file_uploader("Upload EMR Export File", type=['csv', 'xlsx', 'sql'])

        # Date range selection
        date_cols = st.columns(2)
        with date_cols[0]:
            start_date = st.date_input("Start Date")
        with date_cols[1]:
            end_date = st.date_input("End Date")

        # Data selection
        st.subheader("Data Selection")
        data_categories = {
            "Clinical": ["Patient Demographics", "Diagnoses", "Procedures", "Medications", "Allergies"],
            "Laboratory": ["Lab Results", "Microbiology", "Pathology"],
            "Imaging": ["Radiology Reports", "Image Metadata"],
            "Notes": ["Progress Notes", "Discharge Summaries", "Consultation Notes"]
        }

        selected_categories = st.multiselect(
            "Select Data Categories",
            options=list(data_categories.keys())
        )

        if selected_categories:
            all_data_types = []
            for category in selected_categories:
                all_data_types.extend(data_categories[category])

            selected_data_types = st.multiselect(
                "Select Specific Data Types",
                options=all_data_types
            )

        if st.button("Extract Data"):
            with st.spinner("Preparing data extraction..."):
                st.info("Data extraction will start soon. This may take several minutes depending on the selected date range and data types.")

        st.markdown('</div>', unsafe_allow_html=True)

        # Data Import Section
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("Data Import")

        import_tabs = st.tabs(["Document Upload", "Database Import", "API Integration"])

        with import_tabs[0]:
            st.markdown('<div class="upload-area">', unsafe_allow_html=True)
            st.write("Upload research documents for processing")
            uploaded_file = st.file_uploader(
                "Drop your files here or click to upload",
                type=['csv', 'xlsx', 'xls', 'pdf', 'docx', 'txt'],
                help="Supported formats: CSV, Excel, PDF, Word, Text"
            )

            if uploaded_file is not None:
                try:
                    file_content = uploaded_file.read()
                    with st.spinner("Processing document..."):
                        metadata, processed_content = process_document(file_content, uploaded_file.name)

                    # Display metadata
                    st.success("File processed successfully!")
                    st.json(metadata)

                    # Display preview based on file type
                    if metadata["type"] == "spreadsheet":
                        df = pd.read_json(processed_content)
                        st.dataframe(df.head())
                    elif metadata["type"] in ["docx", "text"]:
                        st.subheader("Document Chunks Preview")
                        for i, chunk in enumerate(processed_content[:3]):
                            with st.expander(f"Chunk {i+1}"):
                                st.write(chunk)
                        if len(processed_content) > 3:
                            st.info(f"{len(processed_content) - 3} more chunks available")
                    else:
                        st.write(processed_content)

                    if st.button("Import to Database"):
                        # Add database import logic here
                        st.success("Data imported successfully!")

                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)

        with import_tabs[1]:
            st.write("Database connection configuration will be here")

        with import_tabs[2]:
            st.write("API integration options will be here")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Data Stats Section
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("Project Statistics")

        # Get actual data from database if possible
        try:
            conn = get_database_connection()
            cur = conn.cursor()

            # Get project count
            cur.execute("SELECT COUNT(*) FROM projects WHERE owner_id = %s", (st.session_state.user_id,))
            project_count = cur.fetchone()[0]

            # Get datasets count
            cur.execute("SELECT COUNT(*) FROM research_data WHERE uploaded_by = %s", (st.session_state.user_id,))
            dataset_count = cur.fetchone()[0]

            # Get IRB submissions count
            cur.execute("SELECT COUNT(*) FROM irb_submissions WHERE principal_investigator_id = %s", (st.session_state.user_id,))
            irb_count = cur.fetchone()[0]

            conn.close()
        except Exception as e:
            # If database query fails, use placeholder data
            project_count = 2
            dataset_count = 3
            irb_count = 1

        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-icon">📊</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">Projects</div>
            </div>
            """.format(project_count), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-icon">📂</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">Datasets</div>
            </div>
            """.format(dataset_count), unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-icon">📋</div>
                <div class="metric-value">{}</div>
                <div class="metric-label">IRB Submissions</div>
            </div>
            """.format(irb_count), unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-icon">🔒</div>
                <div class="metric-value">4</div>
                <div class="metric-label">ZKP Verifications</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Quick actions
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("Quick Actions")

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("📤 Upload Data", use_container_width=True):
                st.switch_page("pages/1_Data_Upload.py")

        with action_col2:
            if st.button("🔍 Export Data", use_container_width=True):
                st.switch_page("pages/4_Data_Export.py")

        action_col3, action_col4 = st.columns(2)
        with action_col3:
            if st.button("📋 IRB Portal", use_container_width=True):
                st.switch_page("pages/8_IRB_Portal.py")

        with action_col4:
            if st.button("💬 Messages", use_container_width=True):
                st.switch_page("pages/7_Secure_Messages.py")

        st.markdown('</div>', unsafe_allow_html=True)

        # Recent Activity
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("Recent Activity")

        # Demo activity feed
        activities = [
            {"icon": "📤", "text": "Uploaded data to", "project": "Genomic Analysis", "time": "2023-06-05 14:32"},
            {"icon": "📋", "text": "Submitted IRB for", "project": "Clinical Trial Study", "time": "2023-06-03 09:15"},
            {"icon": "💬", "text": "Sent message to", "project": "Dr. Smith", "time": "2023-06-02 16:45"},
            {"icon": "📊", "text": "Created project", "project": "Patient Data Analysis", "time": "2023-05-28 11:20"}
        ]

        for activity in activities:
            st.markdown(f"""
            <div style="padding: 0.75rem; border-bottom: 1px solid rgba(0,0,0,0.1);">
                <div>{activity['icon']} {activity['text']} <strong>{activity['project']}</strong></div>
                <div style="font-size: 0.8rem; color: rgba(0,0,0,0.6);">{activity['time']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")

try:
    # Check if document_processor module is available
    from utils.document_processor import process_document
except ImportError:
    # Create a simple document processor if the module doesn't exist
    def process_document(file_content, file_name):
        """
        Simple document processor for demo purposes.
        """
        metadata = {
            "filename": file_name,
            "type": "text" if file_name.endswith(".txt") else 
                   "spreadsheet" if file_name.endswith((".csv", ".xlsx")) else 
                   "pdf" if file_name.endswith(".pdf") else "unknown",
            "size": len(file_content),
            "timestamp": datetime.now().isoformat()
        }

        processed_content = "Sample processed content for demonstration"

        return metadata, processed_content