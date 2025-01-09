import streamlit as st
from auth import authenticate_user, create_user, AuthenticationManager
from database import init_database
import os
from PIL import Image
import io
import numpy as np
import json

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
    .auth-step {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .success-message {
        color: #28a745;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
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

def show_auth_step(title, content, status=None):
    """Display an authentication step with status."""
    with st.container():
        col1, col2 = st.columns([5,1])
        with col1:
            st.markdown(f"### {title}")
            st.markdown(content)
        with col2:
            if status == "success":
                st.markdown("✅")
            elif status == "pending":
                st.markdown("⏳")
            elif status == "error":
                st.markdown("❌")

def main():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.auth_step = 'start'
        st.session_state.temp_user_id = None
        st.session_state.passkey_registration = None
        st.session_state.face_verified = False

    if st.session_state.user_id is None:
        st.title("Research Data Management Platform")

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")

            if st.session_state.auth_step == 'start':
                show_auth_step(
                    "Step 1: Passkey Authentication",
                    "Use your device's biometric authentication to verify your identity.",
                    "pending"
                )

                if st.button("Start Authentication"):
                    # In a real implementation, this would trigger the WebAuthn API
                    # For demo purposes, we'll simulate the passkey verification
                    user_id = authenticate_user(username=username, passkey_response={})
                    if user_id:
                        st.session_state.temp_user_id = user_id
                        st.session_state.auth_step = 'face'
                        st.rerun()
                    else:
                        st.error("Passkey authentication failed")

            elif st.session_state.auth_step == 'face':
                show_auth_step(
                    "Step 1: Passkey Authentication",
                    "Device authentication successful",
                    "success"
                )

                show_auth_step(
                    "Step 2: Face Verification",
                    "Please look at the camera or upload a photo for additional verification.",
                    "pending"
                )

                face_file = st.camera_input("Take a photo") or st.file_uploader(
                    "Or upload a photo", 
                    type=['jpg', 'jpeg', 'png'],
                    key="login_face"
                )

                if face_file and st.button("Verify Face"):
                    face_image = process_face_image(face_file)
                    if face_image is not None:
                        user_id = authenticate_user(
                            user_id=st.session_state.temp_user_id,
                            face_image=face_image
                        )
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.auth_step = 'complete'
                            st.success("Authentication successful!")
                            st.rerun()
                        else:
                            st.error("Face verification failed")

        with tab2:
            st.header("Register")
            new_username = st.text_input("Username", key="reg_username")
            new_password = st.text_input("Password", type="password", key="reg_password")
            email = st.text_input("Email")

            if st.session_state.auth_step == 'start':
                st.write("Step 1: Set up face recognition")
                face_file = st.camera_input("Take a photo") or st.file_uploader(
                    "Or upload a photo", 
                    type=['jpg', 'jpeg', 'png'],
                    key="reg_face"
                )

                if st.button("Continue with Registration"):
                    try:
                        face_image = process_face_image(face_file) if face_file else None
                        if face_image is None:
                            st.error("Face image is required for registration")
                            return

                        user_id = create_user(new_username, new_password, email, face_image)
                        st.session_state.temp_user_id = user_id
                        st.session_state.auth_step = 'passkey'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")

            elif st.session_state.auth_step == 'passkey':
                show_auth_step(
                    "Step 1: Face Recognition Setup",
                    "Face recognition configured successfully",
                    "success"
                )

                show_auth_step(
                    "Step 2: Passkey Setup",
                    "Register your device for passwordless login. This will use your device's biometric authentication.",
                    "pending"
                )

                if st.button("Register Passkey"):
                    # Generate registration options
                    options = auth_manager.generate_passkey_registration_options(
                        st.session_state.temp_user_id,
                        new_username
                    )
                    st.session_state.passkey_registration = options

                    # In a real implementation, this would trigger the WebAuthn API
                    # For demo purposes, we'll simulate successful registration
                    try:
                        auth_manager.verify_passkey_registration(
                            st.session_state.temp_user_id,
                            options,
                            {'dummy': 'response'}
                        )
                        st.success("Registration completed successfully! Please login.")
                        st.session_state.auth_step = 'start'
                        st.session_state.temp_user_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Passkey registration failed: {str(e)}")

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