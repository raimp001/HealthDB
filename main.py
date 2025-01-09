import streamlit as st
from auth import authenticate_user, create_user
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

# CSS styling
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton button {
        background-color: #0066cc;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if st.session_state.user_id is None:
        st.title("Research Data Management Platform")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.header("Login")
            use_zkp = st.checkbox("Use Password-less Authentication (ZKP)")
            username = st.text_input("Username", key="login_username")

            if not use_zkp:
                password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login"):
                if use_zkp:
                    user_id = authenticate_user(username, None, use_zkp=True)
                else:
                    user_id = authenticate_user(username, password, use_zkp=False)

                if user_id:
                    st.session_state.user_id = user_id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Authentication failed")

        with tab2:
            st.header("Register")
            new_username = st.text_input("Username", key="reg_username")
            new_password = st.text_input("Password", type="password", key="reg_password")
            email = st.text_input("Email")

            if st.button("Register"):
                try:
                    user_id = create_user(new_username, new_password, email)
                    st.success("Registration successful! Please login.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")

    else:
        st.sidebar.success("Navigate through the pages using the sidebar menu.")
        st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

        st.title("Welcome to the Research Data Platform")
        st.write("""
        This platform provides secure research data management capabilities:

        - Upload and manage research data
        - Create interactive visualizations
        - Manage research projects
        - Export data securely
        - Password-less authentication using Zero-Knowledge Proofs

        Use the sidebar to navigate through different features.
        """)

if __name__ == "__main__":
    main()