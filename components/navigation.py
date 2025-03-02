import streamlit as st

def render_navigation():
    """
    Renders a consistent navigation sidebar across all pages
    with simple styling and no symbols.
    """
    # Add app name with plain styling
    st.sidebar.markdown("""
        <div style="margin-bottom: 1rem;">
            <div style="font-weight: bold; font-size: 1.2rem;">Research Platform</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Secure collaboration</div>
        </div>
    """, unsafe_allow_html=True)

    # User information if logged in
    if 'user_id' in st.session_state and st.session_state.user_id is not None:
        st.sidebar.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 1.5rem; padding: 0.75rem; background-color: rgba(108, 99, 255, 0.1); border-radius: 0.5rem;">
                <div>
                    <div style="font-weight: 500;">{st.session_state.username}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Demo User</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Navigation sections with plain text
    st.sidebar.markdown("### Main Navigation")

    # Dashboard
    if st.sidebar.button("Dashboard", use_container_width=True):
        st.switch_page("main.py")

    # Data Management
    st.sidebar.markdown("### Data Management")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Upload", use_container_width=True):
            st.switch_page("pages/1_Data_Upload.py")
    with col2:
        if st.button("Export", use_container_width=True):
            st.switch_page("pages/4_Data_Export.py")

    # Projects
    st.sidebar.markdown("### Projects")
    if st.sidebar.button("Management", use_container_width=True):
        st.switch_page("pages/3_Project_Management.py")

    # Compliance & Communication
    st.sidebar.markdown("### Compliance & Communication")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("IRB Portal", use_container_width=True):
            st.switch_page("pages/8_IRB_Portal.py")
    with col2:
        if st.button("Messages", use_container_width=True):
            st.switch_page("pages/7_Secure_Messages.py")

    # ZKP Demo
    st.sidebar.markdown("### Privacy & Security")
    if st.sidebar.button("ZKP Demo", use_container_width=True):
        # Check if page exists before redirecting
        try:
            st.switch_page("pages/5_ZKP_Demo.py")
        except:
            st.sidebar.error("ZKP Demo page is not yet available")

    # Footer with version info
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        <div style="font-size: 0.8rem; opacity: 0.8; text-align: center;">
            Research Platform v1.0<br>
            Built with Streamlit
        </div>
    """, unsafe_allow_html=True)