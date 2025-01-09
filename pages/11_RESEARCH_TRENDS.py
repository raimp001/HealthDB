# Previous content remains unchanged
def research_trends_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access research trends.")
        return
    
    st.title("RESEARCH TRENDS ANALYSIS")
    # Rest of the file remains unchanged
