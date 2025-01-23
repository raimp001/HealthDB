import streamlit as st

# Page config
st.set_page_config(
    page_title="Research Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_upload' not in st.session_state:
    st.session_state.show_upload = False
if 'show_viz' not in st.session_state:
    st.session_state.show_viz = False

try:
    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        else:
            st.write(f"Assistant: {message['content']}")

    # Input section with minimal symbols
    col1, col2, col3, col4 = st.columns([0.1, 1, 0.1, 0.1])

    with col1:
        if st.button("⊕"):  # Simple plus symbol
            st.session_state.show_upload = True

    with col2:
        user_input = st.text_input("Send a message", key="user_input")

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

    # Handle file upload
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