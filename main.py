import streamlit as st

# Page config
st.set_page_config(
    page_title="Research Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-container {
        max-width: 1200px;
        margin: auto;
        padding: 2rem;
    }
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        margin-bottom: 2rem;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1E1E2F;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #252525;
        margin-left: 2rem;
        border-left: 4px solid #6C63FF;
    }
    .assistant-message {
        background-color: #1E1E2F;
        margin-right: 2rem;
        border-left: 4px solid #2E7D32;
    }
    .message-content {
        color: #FFFFFF;
        font-size: 1rem;
        line-height: 1.5;
    }
    .control-panel {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #252525;
    }
    .input-area {
        background-color: #1E1E2F;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .stTextInput > div > div > input {
        background-color: #1E1E2F;
        color: white;
        border: 1px solid #6C63FF;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    .stButton > button {
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: transparent;
        border: 1px solid #6C63FF;
        color: white;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #6C63FF;
        color: white;
        transform: translateY(-1px);
    }
    .tool-section {
        padding: 1rem;
        background-color: #252525;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_upload' not in st.session_state:
    st.session_state.show_upload = False
if 'show_viz' not in st.session_state:
    st.session_state.show_viz = False

try:
    st.title("Research Assistant")

    # Main chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Display messages with improved styling
        for message in st.session_state.messages:
            message_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f"""
                <div class="chat-message {message_class}">
                    <div class="message-content">
                        {message['content']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Input and controls section
    with st.container():
        st.markdown('<div class="input-area">', unsafe_allow_html=True)

        # Control panel with tools
        cols = st.columns([0.1, 1, 0.1, 0.1])

        with cols[0]:
            if st.button("⊕", help="Upload files"):
                st.session_state.show_upload = True

        with cols[1]:
            user_input = st.text_input(
                "",
                placeholder="Type your message here...",
                key="user_input"
            )

        with cols[2]:
            if st.button("→", help="Send message"):
                if user_input:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    bot_response = f"I received: {user_input}"
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    st.experimental_rerun()

        with cols[3]:
            if st.button("≡", help="Show visualizations"):
                st.session_state.show_viz = True

        st.markdown('</div>', unsafe_allow_html=True)

    # Tool sections
    if st.session_state.show_upload:
        with st.container():
            st.markdown('<div class="tool-section">', unsafe_allow_html=True)
            st.subheader("Upload Files")
            uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt'])
            if uploaded_file is not None:
                st.success(f"File {uploaded_file.name} uploaded successfully!")
                st.session_state.show_upload = False
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.show_viz:
        with st.container():
            st.markdown('<div class="tool-section">', unsafe_allow_html=True)
            st.subheader("Visualizations")
            st.write("Visualization options will appear here")
            st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")