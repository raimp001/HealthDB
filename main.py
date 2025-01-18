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

# CSS styling based on Aleo guidelines
st.markdown("""
    <style>
    /* Typography */
    body {
        font-family: 'Inter', sans-serif;
        color: #121212;  /* Coal */
        line-height: 1.5;
    }

    /* Main container */
    .main {
        background-color: #E3E3E3;  /* Stone */
        padding: 1rem;
    }

    /* Chat container */
    .chat-container {
        background-color: #F5F5F5;  /* Ivory */
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        height: 70vh;
        overflow-y: auto;
    }

    /* Message bubbles */
    .user-message {
        background-color: #C4F652;  /* Lime */
        color: #121212;  /* Coal */
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        max-width: 80%;
        float: right;
        clear: both;
    }

    .bot-message {
        background-color: #E3E3E3;  /* Stone */
        color: #121212;  /* Coal */
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
        background-color: #F5F5F5;  /* Ivory */
        border-radius: 8px;
        margin-top: 1rem;
    }

    /* Action buttons */
    .action-button {
        background-color: #121212;  /* Coal */
        color: #C4F652;  /* Lime */
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
        font-size: 1.2rem;
    }

    .action-button:hover {
        background-color: #2A2A2A;
        transform: scale(1.05);
    }

    /* Input area */
    .stTextInput {
        flex-grow: 1;
    }

    .stTextInput input {
        border: 2px solid #E3E3E3;  /* Stone */
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
        width: 100%;
    }

    .stTextInput input:focus {
        border-color: #C4F652;  /* Lime */
        box-shadow: 0 0 0 2px rgba(196, 246, 82, 0.2);
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

    # Input area with action buttons
    col1, col2, col3, col4 = st.columns([0.1, 1, 0.1, 0.1])

    with col1:
        st.markdown("""
            <button class="action-button" onclick="handleUpload()">
                📎
            </button>
        """, unsafe_allow_html=True)

    with col2:
        user_input = st.text_input("Send a message", key="user_input")

    with col3:
        st.markdown("""
            <button class="action-button" onclick="handleSend()">
                ⬆️
            </button>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <button class="action-button" onclick="handleVisualize()">
                📈
            </button>
        """, unsafe_allow_html=True)

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Add bot response (placeholder)
        bot_response = f"I received: {user_input}"
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Clear input
        st.experimental_rerun()

    # Handle file upload
    if st.session_state.show_upload:
        uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt'])
        if uploaded_file is not None:
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            st.session_state.show_upload = False

    # Handle visualization
    if st.session_state.show_viz:
        st.write("Visualization options will appear here")

    # JavaScript for handling button clicks
    st.markdown("""
        <script>
        function handleUpload() {
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: true, key: 'show_upload'}, '*');
        }

        function handleVisualize() {
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: true, key: 'show_viz'}, '*');
        }

        function handleSend() {
            // Trigger enter key press on input
            const input = document.querySelector('input[aria-label="Send a message"]');
            if (input && input.value) {
                const event = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    which: 13,
                    keyCode: 13,
                    bubbles: true
                });
                input.dispatchEvent(event);
            }
        }
        </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()