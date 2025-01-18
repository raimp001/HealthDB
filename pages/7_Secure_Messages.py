import streamlit as st
from utils.messaging import SecureMessaging, send_message, get_messages, mark_message_as_read
from database import get_database_connection
import pandas as pd
from datetime import datetime
import pytz

def get_available_recipients():
    """Get list of available users to message."""
    conn = get_database_connection()
    query = """
        SELECT id, username, institution 
        FROM users 
        WHERE id != %s
        ORDER BY username;
    """
    df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
    conn.close()
    return df

def format_timestamp(ts):
    """Format timestamp for display."""
    if ts:
        utc = pytz.UTC
        if not ts.tzinfo:
            ts = utc.localize(ts)
        return ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    return ""

def messages_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access secure messaging.")
        return

    st.title("Secure Research Messages")
    
    # Initialize session state for selected recipient
    if 'selected_recipient' not in st.session_state:
        st.session_state.selected_recipient = None
    
    # Get available recipients
    recipients_df = get_available_recipients()
    
    # Sidebar for recipient selection
    with st.sidebar:
        st.header("Start New Conversation")
        recipient_options = recipients_df.apply(
            lambda x: f"{x['username']} ({x['institution']})", axis=1
        ).tolist()
        recipient_options.insert(0, "Select a researcher")
        
        selected_option = st.selectbox(
            "Choose recipient",
            options=recipient_options,
            key="recipient_selector"
        )
        
        if selected_option != "Select a researcher":
            selected_idx = recipient_options.index(selected_option) - 1
            st.session_state.selected_recipient = recipients_df.iloc[selected_idx]['id']

    # Main message area
    if st.session_state.selected_recipient:
        recipient_info = recipients_df[
            recipients_df['id'] == st.session_state.selected_recipient
        ].iloc[0]
        
        st.header(f"Conversation with {recipient_info['username']}")
        
        # Message composition
        with st.container():
            message_text = st.text_area("Compose Message", height=100)
            if st.button("Send Secure Message"):
                try:
                    # In production, implement proper key management
                    secure_messaging = SecureMessaging()
                    recipient_key = None  # Placeholder for recipient's public key
                    
                    success = send_message(
                        st.session_state.user_id,
                        st.session_state.selected_recipient,
                        message_text,
                        recipient_key
                    )
                    
                    if success:
                        st.success("Message sent securely!")
                        st.rerun()
                    else:
                        st.error("Failed to send message")
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
        
        # Message history
        st.subheader("Message History")
        messages = get_messages(
            st.session_state.user_id,
            st.session_state.selected_recipient
        )
        
        for msg in messages:
            with st.container():
                col1, col2 = st.columns([5,1])
                
                is_sender = msg['sender_id'] == st.session_state.user_id
                
                with col1:
                    # Message container with different styling for sent/received
                    message_style = """
                        <div style='
                            padding: 10px;
                            border-radius: 10px;
                            margin: 5px;
                            background-color: {};
                            text-align: {};
                            max-width: 80%;
                            float: {};
                        '>
                            <strong>{}</strong><br>
                            {}
                        </div>
                        <div style='clear: both;'></div>
                    """.format(
                        "#e3f2fd" if is_sender else "#f5f5f5",
                        "right" if is_sender else "left",
                        "right" if is_sender else "left",
                        "You" if is_sender else msg['sender_username'],
                        msg['encrypted_content']  # In production, implement decryption
                    )
                    st.markdown(message_style, unsafe_allow_html=True)
                
                with col2:
                    st.caption(format_timestamp(msg['created_at']))
                    if msg['read_at']:
                        st.caption("✓ Read")
                    elif not is_sender:
                        mark_message_as_read(msg['id'], st.session_state.user_id)
    
    else:
        st.info("Select a researcher from the sidebar to start a secure conversation.")
        
        # Show message preview
        st.subheader("Recent Messages")
        messages = get_messages(st.session_state.user_id)
        
        if messages:
            for msg in messages[:5]:  # Show last 5 messages
                with st.container():
                    preview_style = f"""
                        <div style='
                            padding: 10px;
                            border-radius: 5px;
                            margin: 5px;
                            background-color: #f8f9fa;
                            cursor: pointer;
                        '>
                            <strong>{msg['sender_username']} → {msg['recipient_username']}</strong><br>
                            <small>{format_timestamp(msg['created_at'])}</small>
                        </div>
                    """
                    st.markdown(preview_style, unsafe_allow_html=True)
        else:
            st.write("No messages yet")

if __name__ == "__main__":
    messages_page()
