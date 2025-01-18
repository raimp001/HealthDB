import streamlit as st
from database import init_database
import os

# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="Research Data Management Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling based on Aleo guidelines
st.markdown("""
    <style>
    /* Typography */
    body {
        font-family: 'Inter', sans-serif;
        color: #121212;  /* Coal */
        line-height: 1.5;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #121212;  /* Coal */
        margin-bottom: 1.5rem;
    }

    /* Layout and Spacing */
    .main {
        background-color: #E3E3E3;  /* Stone */
        padding: 2rem;
    }
    .block-container {
        padding: 2rem;
    }

    /* Buttons */
    .stButton button {
        background-color: #121212;  /* Coal */
        color: #C4F652;  /* Lime */
        border: none;
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #2A2A2A;
        transform: translateY(-1px);
    }

    /* Sidebar Navigation */
    .css-1d391kg {  /* Sidebar class */
        background-color: #121212;  /* Coal */
        padding: 1rem;
    }
    .css-1d391kg .stButton button {
        background-color: #C4F652;  /* Lime */
        color: #121212;  /* Coal */
    }

    /* Navigation Groups */
    .sidebar-group {
        margin-bottom: 1.5rem;
        padding: 1rem;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.05);
    }

    .sidebar-group-title {
        color: #C4F652;  /* Lime */
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }

    /* Navigation Links */
    .css-1d391kg a {
        color: #F5F5F5;  /* Ivory */
        text-decoration: none;
        display: block;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .css-1d391kg a:hover {
        background-color: rgba(196, 246, 82, 0.1);  /* Lime with opacity */
        color: #C4F652;  /* Lime */
    }

    .css-1d391kg a.active {
        background-color: #C4F652;  /* Lime */
        color: #121212;  /* Coal */
    }

    /* Form Elements */
    .stTextInput input, .stTextArea textarea {
        border: 2px solid #E3E3E3;  /* Stone */
        border-radius: 4px;
        padding: 0.75rem;
        transition: border-color 0.2s ease;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #C4F652;  /* Lime */
        box-shadow: 0 0 0 2px rgba(196, 246, 82, 0.2);  /* Lime with opacity */
    }

    /* Dropdown Styles */
    .stSelectbox {
        margin-bottom: 1rem;
    }
    .stSelectbox > div > div {
        background-color: #F5F5F5;  /* Ivory */
        border: 2px solid #E3E3E3;  /* Stone */
        border-radius: 4px;
    }
    .stSelectbox > div > div:hover {
        border-color: #C4F652;  /* Lime */
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Set default user session for development
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1  # Default user ID for development

    # Sidebar Navigation
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-group">
                <div class="sidebar-group-title">Research Tools</div>
                <a href="/" class="active">Home</a>
                <a href="1_Data_Upload">Data Upload</a>
                <a href="2_Visualizations">Visualizations</a>
                <a href="3_Project_Management">Project Management</a>
                <a href="4_Data_Export">Data Export</a>
            </div>

            <div class="sidebar-group">
                <div class="sidebar-group-title">Advanced Features</div>
                <a href="5_ZKP_Demo">ZKP Demo</a>
                <a href="6_Researcher_Profile">Researcher Profile</a>
                <a href="7_Secure_Messages">Secure Messages</a>
                <a href="8_Citation_Tool">Citation Tool</a>
                <a href="9_Message_Analytics">Message Analytics</a>
                <a href="10_Literature_Review_Assistant">Literature Review</a>
            </div>
        """, unsafe_allow_html=True)

    # Main content area
    st.title("Research Data Platform")
    st.write("""
    Welcome to the Research Data Platform! This platform provides advanced tools for:

    - Data management and visualization
    - Secure collaboration between researchers
    - AI-powered literature review assistance
    - Zero-knowledge proof demonstrations
    - Citation management

    Use the sidebar navigation to explore different features.
    """)

    # Feature highlights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### Data Management
        Upload, visualize, and manage your research data securely.
        """)

    with col2:
        st.markdown("""
        ### Collaboration
        Connect with other researchers and share insights safely.
        """)

    with col3:
        st.markdown("""
        ### AI Assistant
        Get AI-powered help with literature reviews and analysis.
        """)

if __name__ == "__main__":
    main()