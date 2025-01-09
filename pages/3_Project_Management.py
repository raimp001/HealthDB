import streamlit as st

def project_management_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Project Management")
    # Rest of the file remains unchanged
