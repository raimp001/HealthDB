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
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #1E1E2F;
        margin-left: 2rem;
        margin-right: 1rem;
        border-left: 4px solid #6C63FF;
    }
    .assistant-message {
        background-color: #252525;
        margin-left: 1rem;
        margin-right: 2rem;
        border-left: 4px solid #2E7D32;
    }
    .message-content {
        color: #FFFFFF;
        font-size: 1rem;
    }
    .stTextInput > div > div > input {
        background-color: #1E1E2F;
        color: white;
        border: 1px solid #6C63FF;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
    }
    .stButton > button {
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: transparent;
        border: 1px solid #6C63FF;
        color: white;
    }
    .stButton > button:hover {
        background-color: #6C63FF;
        color: white;
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

    # Input section with minimal symbols
    col1, col2, col3, col4 = st.columns([0.1, 1, 0.1, 0.1])

    with col1:
        if st.button("⊕"):  # Simple plus symbol
            st.session_state.show_upload = True

    with col2:
        user_input = st.text_input("", placeholder="Type your message here...", key="user_input")

    with col3:
        if st.button("→"):  # Simple arrow
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = f"I received: {user_input}"
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.experimental_rerun()

    with col4:
        if st.button("≡"):  # Simple menu symbol
            st.session_state.show_viz = True

    # Handle file upload with improved styling
    if st.session_state.show_upload:
        uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'txt'])
        if uploaded_file is not None:
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            st.session_state.show_upload = False

    # Handle visualization
    if st.session_state.show_viz:
        st.write("Visualization options will appear here")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")