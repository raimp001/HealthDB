import streamlit as st

def researcher_profile_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Researcher Profile")
    # Rest of the file remains unchanged
