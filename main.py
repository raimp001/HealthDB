import streamlit as st
import pandas as pd
from utils.document_processor import process_document
import json
from database import init_database, get_database_connection
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

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
    .dashboard-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }

    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .dashboard-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1E1E2F;
        margin: 0;
    }

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

    /* Activity feed */
    .activity-item {
        padding: 0.75rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
    }

    .activity-item:last-child {
        border-bottom: none;
    }

    .activity-time {
        font-size: 0.8rem;
        color: rgba(49, 51, 63, 0.6);
    }

    /* Quick actions */
    .action-button {
        background-color: #f8f9fa;
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        height: 100%;
    }

    .action-button:hover {
        background-color: #6C63FF;
        color: white;
    }

    .action-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    /* User info */
    .user-info {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }

    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #6C63FF;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

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

# Main dashboard layout
col1, col2 = st.columns([2, 1])

with col1:
    # Key metrics
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">Research Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

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

        # Get collaborators count
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM collaborations 
            WHERE project_id IN (SELECT id FROM projects WHERE owner_id = %s)
        """, (st.session_state.user_id,))
        collaborator_count = cur.fetchone()[0]

        conn.close()
    except Exception as e:
        # If database query fails, use placeholder data
        project_count = 2
        dataset_count = 3
        irb_count = 1
        collaborator_count = 2

    # Display metrics in a grid
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Projects</div>
        </div>
        """.format(project_count), unsafe_allow_html=True)

    with metric_col2:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-icon">📂</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Datasets</div>
        </div>
        """.format(dataset_count), unsafe_allow_html=True)

    with metric_col3:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">IRB Submissions</div>
        </div>
        """.format(irb_count), unsafe_allow_html=True)

    with metric_col4:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Collaborators</div>
        </div>
        """.format(collaborator_count), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Recent projects with data visualization
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">Recent Projects</h2>
    </div>
    """, unsafe_allow_html=True)

    # Get recent projects data
    try:
        conn = get_database_connection()
        query = """
            SELECT p.id, p.name, p.description, p.created_at, 
                   COUNT(DISTINCT rd.id) as data_count,
                   COUNT(DISTINCT c.user_id) as collaborator_count
            FROM projects p
            LEFT JOIN research_data rd ON p.id = rd.project_id
            LEFT JOIN collaborations c ON p.id = c.project_id
            WHERE p.owner_id = %s
            GROUP BY p.id, p.name, p.description, p.created_at
            ORDER BY p.created_at DESC
            LIMIT 5;
        """

        projects_df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()

        if len(projects_df) > 0:
            for _, row in projects_df.iterrows():
                st.write(f"### {row['name']}")
                st.write(f"{row['description']}")

                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"Created: {row['created_at'].strftime('%Y-%m-%d')}")
                with col2:
                    st.metric("Datasets", row['data_count'])
                with col3:
                    st.metric("Collaborators", row['collaborator_count'])

                st.markdown("---")
        else:
            st.info("No projects found. Create a new project to get started.")

    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")
        # Show demo projects
        st.write("### Genomic Analysis")
        st.write("Analysis of genomic data for rare diseases")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write("Created: 2023-01-15")
        with col2:
            st.metric("Datasets", 2)
        with col3:
            st.metric("Collaborators", 3)

        st.markdown("---")

        st.write("### Clinical Trial Data")
        st.write("Multi-center trial data repository")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write("Created: 2023-03-22")
        with col2:
            st.metric("Datasets", 1)
        with col3:
            st.metric("Collaborators", 2)

    st.markdown('</div>', unsafe_allow_html=True)

    # Data visualization
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">Research Data Overview</h2>
    </div>
    """, unsafe_allow_html=True)

    # Generate sample data for visualization if real data not available
    try:
        # Try to get actual data from database
        conn = get_database_connection()
        query = """
            SELECT data_type, COUNT(*) as count, 
                   DATE_TRUNC('month', uploaded_at) as month
            FROM research_data
            WHERE uploaded_by = %s
            GROUP BY data_type, DATE_TRUNC('month', uploaded_at)
            ORDER BY month;
        """
        data_df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()

        if len(data_df) > 0:
            # Create visualization with real data
            fig = px.bar(data_df, x="month", y="count", color="data_type", 
                         title="Data Uploads by Month and Type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Create sample data
            raise Exception("No data available")

    except Exception:
        # Create sample data for demonstration
        dates = pd.date_range(start=datetime.now() - timedelta(days=180), 
                             end=datetime.now(), freq='M')
        data_types = ['csv', 'json', 'excel', 'text']

        data = []
        for date in dates:
            for dtype in data_types:
                count = np.random.randint(0, 5)
                if count > 0:  # Only add entries with data
                    data.append({
                        'month': date,
                        'data_type': dtype,
                        'count': count
                    })

        demo_df = pd.DataFrame(data)

        fig = px.bar(demo_df, x="month", y="count", color="data_type", 
                     title="Data Uploads by Month and Type (Demo Data)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # Quick actions
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">Quick Actions</h2>
    </div>
    """, unsafe_allow_html=True)

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

    # Activity feed
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">Recent Activity</h2>
    </div>
    """, unsafe_allow_html=True)

    # Try to get actual activity data
    try:
        conn = get_database_connection()
        query = """
            SELECT 'data_upload' as activity_type, 
                   rd.uploaded_at as timestamp,
                   p.name as project_name
            FROM research_data rd
            JOIN projects p ON rd.project_id = p.id
            WHERE rd.uploaded_by = %s
            UNION ALL
            SELECT 'irb_submission' as activity_type,
                   is.submitted_at as timestamp,
                   is.title as project_name
            FROM irb_submissions is
            WHERE is.principal_investigator_id = %s
            ORDER BY timestamp DESC
            LIMIT 10;
        """
        activity_df = pd.read_sql(query, conn, params=(st.session_state.user_id, st.session_state.user_id))
        conn.close()

        if len(activity_df) > 0:
            for _, row in activity_df.iterrows():
                activity_icon = "📤" if row['activity_type'] == "data_upload" else "📋"
                activity_text = f"Uploaded data to" if row['activity_type'] == "data_upload" else "Submitted IRB for"

                st.markdown(f"""
                <div class="activity-item">
                    <div>{activity_icon} {activity_text} <strong>{row['project_name']}</strong></div>
                    <div class="activity-time">{row['timestamp'].strftime('%Y-%m-%d %H:%M')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            raise Exception("No activity data available")

    except Exception:
        # Demo activity feed
        activities = [
            {"icon": "📤", "text": "Uploaded data to", "project": "Genomic Analysis", "time": "2023-06-05 14:32"},
            {"icon": "📋", "text": "Submitted IRB for", "project": "Clinical Trial Study", "time": "2023-06-03 09:15"},
            {"icon": "💬", "text": "Sent message to", "project": "Dr. Smith", "time": "2023-06-02 16:45"},
            {"icon": "📊", "text": "Created project", "project": "Patient Data Analysis", "time": "2023-05-28 11:20"},
            {"icon": "🔒", "text": "Updated permissions for", "project": "Genomic Analysis", "time": "2023-05-25 13:10"}
        ]

        for activity in activities:
            st.markdown(f"""
            <div class="activity-item">
                <div>{activity['icon']} {activity['text']} <strong>{activity['project']}</strong></div>
                <div class="activity-time">{activity['time']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Zero-knowledge proof status
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

    st.markdown("""
    <div class="dashboard-header">
        <h2 class="dashboard-title">ZKP Verification Status</h2>
    </div>
    """, unsafe_allow_html=True)

    # Sample ZKP verification status
    zkp_statuses = [
        {"data": "Genomic Dataset", "status": "Verified", "date": "2023-06-01"},
        {"data": "Patient Records", "status": "Pending", "date": "2023-06-05"}
    ]

    for zkp in zkp_statuses:
        status_color = "green" if zkp["status"] == "Verified" else "orange"
        status_icon = "✅" if zkp["status"] == "Verified" else "⏳"

        st.markdown(f"""
        <div style="padding: 0.75rem; margin-bottom: 0.5rem; border-left: 3px solid {status_color}; background-color: rgba(0,0,0,0.05);">
            <div><strong>{zkp['data']}</strong></div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {status_color};">{status_icon} {zkp['status']}</span>
                <span class="activity-time">{zkp['date']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

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