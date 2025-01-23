import streamlit as st
from database import init_database
import os

# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS styling - minimal version
st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 1rem;
    }

    /* Chat container */
    .chat-container {
        padding: 1rem;
        margin-bottom: 1rem;
        height: 70vh;
        overflow-y: auto;
    }

    /* Message bubbles */
    .user-message {
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        max-width: 80%;
        float: right;
        clear: both;
    }

    .bot-message {
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        max-width: 80%;
        float: left;
        clear: both;
    }

    /* Input container */
    .input-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Set default user session for development
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'show_upload' not in st.session_state:
        st.session_state.show_upload = False
    if 'show_viz' not in st.session_state:
        st.session_state.show_viz = False

    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Input section with buttons
    st.markdown('<div class="input-container">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([0.1, 1, 0.1, 0.1])

    with col1:
        if st.button("📎"):
            st.session_state.show_upload = True

    with col2:
        user_input = st.text_input("Send a message", key="user_input")

    with col3:
        if st.button("⬆️"):
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = f"I received: {user_input}"
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.experimental_rerun()

    with col4:
        if st.button("📈"):
            st.session_state.show_viz = True

    st.markdown('</div>', unsafe_allow_html=True)

    # Handle file upload
    if st.session_state.show_upload:
        uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt'])
        if uploaded_file is not None:
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            st.session_state.show_upload = False

    # Handle visualization
    if st.session_state.show_viz:
        st.write("Visualization options will appear here")

if __name__ == "__main__":
    main()