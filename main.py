import streamlit as st
from auth import authenticate_user, create_user, AuthenticationManager
from database import init_database
import os
from PIL import Image
import io
import numpy as np

# Initialize database
init_database()

# Initialize authentication manager
auth_manager = AuthenticationManager()

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
    .auth-method {
        margin: 10px 0;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

def process_face_image(uploaded_file):
    """Process uploaded face image."""
    if uploaded_file is None:
        return None

    image = Image.open(uploaded_file)
    image_array = np.array(image)
    return image_array

def main():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.passkey_options = None

    if st.session_state.user_id is None:
        st.title("Research Data Management Platform")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")

            # Authentication method selection
            auth_method = st.radio(
                "Choose Authentication Method",
                ["Password", "Face Recognition", "Passkey", "Zero-Knowledge Proof"],
                horizontal=True
            )

            if auth_method == "Password":
                password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login with Password"):
                    user_id = authenticate_user(username, password=password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Authentication failed")

            elif auth_method == "Face Recognition":
                st.write("Please look at the camera or upload a photo")
                face_file = st.camera_input("Take a photo") or st.file_uploader("Or upload a photo", type=['jpg', 'jpeg', 'png'])

                if face_file and st.button("Login with Face"):
                    face_image = process_face_image(face_file)
                    if face_image is not None:
                        user_id = authenticate_user(username, face_image=face_image)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.success("Face recognition successful!")
                            st.rerun()
                        else:
                            st.error("Face recognition failed")

            elif auth_method == "Passkey":
                if st.button("Login with Passkey"):
                    # Generate passkey authentication options
                    options = auth_manager.generate_passkey_auth_options()
                    st.session_state.passkey_options = options

                    # In a real implementation, you would handle the WebAuthn API calls here
                    st.info("Passkey authentication would be triggered here")
                    # For demo purposes, we'll simulate successful authentication
                    user_id = authenticate_user(username, passkey_response={})
                    if user_id:
                        st.session_state.user_id = user_id
                        st.success("Passkey authentication successful!")
                        st.rerun()

            elif auth_method == "Zero-Knowledge Proof":
                if st.button("Login with ZKP"):
                    user_id = authenticate_user(username, use_zkp=True)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.success("ZKP authentication successful!")
                        st.rerun()
                    else:
                        st.error("Authentication failed")

        with tab2:
            st.header("Register")
            new_username = st.text_input("Username", key="reg_username")
            new_password = st.text_input("Password", type="password", key="reg_password")
            email = st.text_input("Email")

            st.write("Optional: Set up face recognition")
            face_file = st.camera_input("Take a photo") or st.file_uploader("Or upload a photo", type=['jpg', 'jpeg', 'png'])

            if st.button("Register"):
                try:
                    face_image = process_face_image(face_file) if face_file else None
                    user_id = create_user(new_username, new_password, email, face_image)
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
        - Multi-factor authentication with face recognition and passkeys
        - Password-less authentication using Zero-Knowledge Proofs

        Use the sidebar to navigate through different features.
        """)

if __name__ == "__main__":
    main()