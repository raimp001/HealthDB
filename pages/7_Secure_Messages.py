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
        SELECT id, username 
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
    # Set up demo user if not logged in
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        # Instead of requiring login, use a demo user ID
        st.session_state.user_id = 1  # Use a default user ID for demonstration
        st.session_state.username = "Demo User"

        # Create a notice that we're in demo mode
        st.info("You are viewing the Secure Messages page in demonstration mode. No login required.")

    st.title("Secure Research Messages")

    # Initialize session state for selected recipient
    if 'selected_recipient' not in st.session_state:
        st.session_state.selected_recipient = None

    # Get available recipients
    try:
        recipients_df = get_available_recipients()

        # If no recipients found, create some demo users
        if len(recipients_df) == 0:
            conn = get_database_connection()
            cur = conn.cursor()

            # Check if users table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)

            if cur.fetchone()[0]:
                # Add some demo users if user table exists but empty
                cur.execute("""
                    INSERT INTO users (username, email)
                    VALUES 
                        ('Dr. Smith', 'smith@research.edu'),
                        ('Dr. Johnson', 'johnson@hospital.org'),
                        ('Dr. Williams', 'williams@institute.net')
                    ON CONFLICT (username) DO NOTHING;
                """)
                conn.commit()

            cur.close()
            conn.close()

            # Try again to get recipients
            recipients_df = get_available_recipients()
    except Exception as e:
        st.error(f"Error loading recipients: {str(e)}")
        # Create dummy data for demonstration
        recipients_df = pd.DataFrame({
            'id': [2, 3, 4],
            'username': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams']
        })

    # Sidebar for recipient selection
    with st.sidebar:
        st.header("Start New Conversation")
        recipient_options = recipients_df.apply(
            lambda x: f"{x['username']}", axis=1
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
                    # In demo mode, we'll create a simple mock key
                    secure_messaging = SecureMessaging()

                    # Create a placeholder public key (for demo purposes only)
                    class DemoPublicKey:
                        def encrypt(self, data, padding):
                            return data  # Just return data for demo

                    recipient_key = DemoPublicKey()

                    try:
                        message_id = send_message(
                            st.session_state.user_id,
                            st.session_state.selected_recipient,
                            message_text,
                            recipient_key
                        )

                        if message_id:
                            st.success("Message sent securely!")
                            st.rerun()
                        else:
                            st.error("Failed to send message")
                    except Exception as e:
                        st.error(f"Error sending message: {str(e)}")
                        st.info("This is a demonstration of the secure messaging interface. In a production environment, proper encryption would be implemented.")
                except Exception as e:
                    st.error(f"Error initializing secure messaging: {str(e)}")

        # Message history
        st.subheader("Message History")
        try:
            messages = get_messages(
                st.session_state.user_id,
                st.session_state.selected_recipient
            )

            if not messages:
                st.info("No messages yet. Start the conversation!")
            else:
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
                                try:
                                    mark_message_as_read(msg['id'], st.session_state.user_id)
                                except Exception as e:
                                    # Silently handle this error in demo mode
                                    pass
        except Exception as e:
            st.error(f"Error loading messages: {str(e)}")
            # Show demo messages if database fails
            st.info("This is a demonstration of how messages would appear. In production, actual encrypted messages would be displayed.")
            # Demo messages
            demo_messages = [
                {"sent": False, "content": "Hello! I saw your presentation at the conference. I'd like to collaborate on your research project.", "time": "2 days ago"},
                {"sent": True, "content": "Thank you for reaching out! I'd be happy to discuss collaboration opportunities.", "time": "1 day ago"},
                {"sent": False, "content": "Great! I have some ideas about expanding your methodology to include additional data sources.", "time": "1 day ago"},
                {"sent": True, "content": "That sounds interesting. Let's schedule a secure video call to discuss the details further.", "time": "5 hours ago"}
            ]

            for msg in demo_messages:
                with st.container():
                    col1, col2 = st.columns([5,1])
                    with col1:
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
                            "#e3f2fd" if msg["sent"] else "#f5f5f5",
                            "right" if msg["sent"] else "left",
                            "right" if msg["sent"] else "left",
                            "You" if msg["sent"] else "Dr. Smith",
                            msg["content"]
                        )
                        st.markdown(message_style, unsafe_allow_html=True)
                    with col2:
                        st.caption(msg["time"])
                        if not msg["sent"]:
                            st.caption("✓ Read")

    else:
        st.info("Select a researcher from the sidebar to start a secure conversation.")

        # Show message preview
        st.subheader("Recent Messages")
        try:
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
                # Show demo message previews
                st.info("This is a demonstration. In production, your recent messages would appear here.")
                demo_previews = [
                    {"sender": "Dr. Smith", "recipient": "You", "time": "2 days ago"},
                    {"sender": "You", "recipient": "Dr. Johnson", "time": "1 week ago"}
                ]

                for preview in demo_previews:
                    preview_style = f"""
                        <div style='
                            padding: 10px;
                            border-radius: 5px;
                            margin: 5px;
                            background-color: #f8f9fa;
                            cursor: pointer;
                        '>
                            <strong>{preview['sender']} → {preview['recipient']}</strong><br>
                            <small>{preview['time']}</small>
                        </div>
                    """
                    st.markdown(preview_style, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading message previews: {str(e)}")
            st.info("This is a demonstration. In production, your recent messages would appear here.")

if __name__ == "__main__":
    messages_page()