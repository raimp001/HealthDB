import streamlit as st

def message_analytics_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to view message analytics.")
        return
        
    st.title("Message Analytics")
    # Rest of the file remains unchanged
