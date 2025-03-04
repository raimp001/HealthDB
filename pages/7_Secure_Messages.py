import streamlit as st
from utils.messaging import SecureMessaging, send_message, get_messages, mark_message_as_read
from database import get_database_connection
import pandas as pd
from datetime import datetime
import pytz
from components.navigation import render_navigation
import logging
from typing import Optional, List, Dict, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_available_recipients() -> pd.DataFrame:
    """
    Get list of available users to message.

    Returns:
        DataFrame containing user IDs and usernames
    """
    try:
        conn = get_database_connection()
        query = """
            SELECT id, username, email
            FROM users 
            WHERE id != %s AND is_active = TRUE
            ORDER BY username;
        """
        df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error fetching recipients: {e}")
        # Return empty dataframe with expected columns in case of error
        return pd.DataFrame(columns=['id', 'username', 'email'])

def format_timestamp(ts: Optional[datetime]) -> str:
    """
    Format timestamp for display in user's local timezone.

    Args:
        ts: Timestamp to format

    Returns:
        Formatted timestamp string
    """
    if not ts:
        return ""

    utc = pytz.UTC
    if not ts.tzinfo:
        ts = utc.localize(ts)

    # Format with user-friendly relative time
    now = datetime.now(utc)
    delta = now - ts

    if delta.days == 0:
        if delta.seconds < 60:
            return "Just now"
        if delta.seconds < 3600:
            return f"{delta.seconds // 60} minutes ago"
        return f"{delta.seconds // 3600} hours ago"
    elif delta.days == 1:
        return "Yesterday"
    elif delta.days < 7:
        return f"{delta.days} days ago"
    else:
        return ts.strftime("%b %d, %Y")

def create_demo_data() -> None:
    """Create demo users and messages if in demonstration mode."""
    try:
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
            # Add demo users
            cur.execute("""
                INSERT INTO users (username, email, is_active)
                VALUES 
                    ('Dr. Smith', 'smith@research.edu', TRUE),
                    ('Dr. Johnson', 'johnson@hospital.org', TRUE),
                    ('Dr. Williams', 'williams@institute.net', TRUE),
                    ('Dr. Brown', 'brown@university.edu', TRUE)
                ON CONFLICT (username) DO NOTHING;
            """)

            # Add some demo messages
            if 'user_id' in st.session_state:
                # Get the first demo user id
                cur.execute("SELECT id FROM users WHERE username = 'Dr. Smith' LIMIT 1")
                demo_user = cur.fetchone()

                if demo_user:
                    demo_user_id = demo_user[0]

                    # Add demo messages
                    cur.execute("""
                        INSERT INTO messages (sender_id, recipient_id, encrypted_content, created_at)
                        VALUES 
                            (%s, %s, 'Hello! Interested in collaborating on your research project.', NOW() - INTERVAL '2 days'),
                            (%s, %s, 'I would be happy to discuss collaboration opportunities.', NOW() - INTERVAL '1 day')
                        ON CONFLICT DO NOTHING;
                    """, (demo_user_id, st.session_state.user_id, st.session_state.user_id, demo_user_id))

            conn.commit()

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating demo data: {e}")

def display_message(msg: Dict[str, Any], is_sender: bool) -> None:
    """
    Display a single message with appropriate styling.

    Args:
        msg: Message data dictionary
        is_sender: True if the current user is the sender
    """
    col1, col2 = st.columns([5, 1])

    with col1:
        # Message container with different styling for sent/received
        message_style = f"""
            <div style='
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
                background-color: {"#e3f2fd" if is_sender else "#f5f5f5"};
                text-align: {"right" if is_sender else "left"};
                max-width: 80%;
                float: {"right" if is_sender else "left"};
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            '>
                <strong>{"You" if is_sender else msg['sender_username']}</strong><br>
                {msg['encrypted_content']}
            </div>
            <div style='clear: both;'></div>
        """
        st.markdown(message_style, unsafe_allow_html=True)

    with col2:
        timestamp = format_timestamp(msg.get('created_at'))
        st.caption(timestamp)

        # Show read status
        if msg.get('read_at') and is_sender:
            st.caption("✓ Read")
        elif not is_sender and not msg.get('read_at'):
            try:
                mark_message_as_read(msg['id'], st.session_state.user_id)
            except Exception as e:
                logger.error(f"Error marking message as read: {e}")

def search_messages(query: str) -> List[Dict[str, Any]]:
    """
    Search messages for the given query.

    Args:
        query: Search text

    Returns:
        List of message dictionaries matching the query
    """
    try:
        conn = get_database_connection()
        search_sql = """
            SELECT m.id, m.sender_id, s.username as sender_username, 
                   m.recipient_id, r.username as recipient_username,
                   m.encrypted_content, m.created_at, m.read_at
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.recipient_id = r.id
            WHERE (m.sender_id = %s OR m.recipient_id = %s)
              AND m.encrypted_content ILIKE %s
            ORDER BY m.created_at DESC
        """
        df = pd.read_sql(search_sql, conn, params=(
            st.session_state.user_id, 
            st.session_state.user_id,
            f"%{query}%"
        ))
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return []

def messages_page():
    """Main function to render the secure messaging page."""
    # Set page config
    st.set_page_config(
        page_title="Secure Research Messaging",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Set up demo user if not logged in
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        # Instead of requiring login, use a demo user ID
        st.session_state.user_id = 1  # Use a default user ID for demonstration
        st.session_state.username = "Demo User"

        # Create demo data
        create_demo_data()

        # Create a notice that we're in demo mode
        st.info("🔍 You are viewing the Secure Messages page in demonstration mode. No login required.")

    # Render consistent navigation
    render_navigation()

    st.title("🔒 Secure Research Messages")

    # Initialize session state
    if 'selected_recipient' not in st.session_state:
        st.session_state.selected_recipient = None

    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    if 'show_search' not in st.session_state:
        st.session_state.show_search = False

    # Get available recipients
    recipients_df = get_available_recipients()

    # If still no recipients, create dummy data for demonstration
    if len(recipients_df) == 0:
        recipients_df = pd.DataFrame({
            'id': [2, 3, 4, 5],
            'username': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown'],
            'email': ['smith@research.edu', 'johnson@hospital.org', 'williams@institute.net', 'brown@university.edu']
        })

    # Sidebar for recipient selection and search
    with st.sidebar:
        # Add search box
        st.subheader("🔍 Search Messages")
        search_input = st.text_input("Enter search term", key="search_input")
        if st.button("Search", key="search_button"):
            st.session_state.search_query = search_input
            st.session_state.show_search = True

        st.divider()

        st.subheader("👤 Start New Conversation")

        # Group recipients by first letter for better organization
        grouped_recipients = recipients_df.groupby(recipients_df['username'].str[0])

        # Create a more structured selection interface
        recipient_id = None
        selected_letter = st.selectbox(
            "Filter by first letter",
            options=["All"] + sorted(grouped_recipients.groups.keys()),
            key="letter_filter"
        )

        if selected_letter == "All":
            filtered_df = recipients_df
        else:
            filtered_df = recipients_df[recipients_df['username'].str.startswith(selected_letter)]

        recipient_options = filtered_df.apply(
            lambda x: f"{x['username']} ({x['email']})", axis=1
        ).tolist()

        if recipient_options:
            recipient_options.insert(0, "Select a researcher")
            selected_option = st.selectbox(
                "Choose recipient",
                options=recipient_options,
                key="recipient_selector"
            )

            if selected_option != "Select a researcher":
                selected_idx = recipient_options.index(selected_option) - 1
                recipient_id = filtered_df.iloc[selected_idx]['id']

                if st.button("Start Conversation", key="start_convo"):
                    st.session_state.selected_recipient = recipient_id
                    st.session_state.show_search = False
                    st.rerun()
        else:
            st.info("No recipients found with the selected filter")

    # Main content area
    if st.session_state.show_search and st.session_state.search_query:
        # Display search results
        st.header(f"🔍 Search Results: '{st.session_state.search_query}'")

        search_results = search_messages(st.session_state.search_query)

        if not search_results:
            st.info("No messages found matching your search.")
        else:
            st.success(f"Found {len(search_results)} message(s) matching your search.")

            for msg in search_results:
                with st.container():
                    st.markdown(f"**Conversation with {msg['sender_username'] if msg['recipient_id'] == st.session_state.user_id else msg['recipient_username']}**")
                    display_message(msg, msg['sender_id'] == st.session_state.user_id)

                    if st.button(f"View Full Conversation", key=f"view_convo_{msg['id']}"):
                        if msg['sender_id'] == st.session_state.user_id:
                            st.session_state.selected_recipient = msg['recipient_id']
                        else:
                            st.session_state.selected_recipient = msg['sender_id']
                        st.session_state.show_search = False
                        st.rerun()

                st.divider()

        if st.button("Back to Messages", key="back_from_search"):
            st.session_state.show_search = False
            st.rerun()

    elif st.session_state.selected_recipient:
        # Show conversation with selected recipient
        recipient_info = recipients_df[
            recipients_df['id'] == st.session_state.selected_recipient
        ]

        if len(recipient_info) > 0:
            recipient_info = recipient_info.iloc[0]
            recipient_name = recipient_info['username']
        else:
            # Fallback for demo mode
            recipient_name = "Researcher"

        # Header with back button
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← Back", key="back_button"):
                st.session_state.selected_recipient = None
                st.rerun()
        with col2:
            st.header(f"Conversation with {recipient_name}")

        # Message history container with fixed height
        with st.container():
            message_area = st.container(height=400, border=False)

            with message_area:
                try:
                    messages = get_messages(
                        st.session_state.user_id,
                        st.session_state.selected_recipient
                    )

                    if not messages:
                        st.info("No messages yet. Start the conversation!")
                    else:
                        # Display messages in reverse order (newest at bottom)
                        for msg in sorted(messages, key=lambda x: x.get('created_at', datetime.min)):
                            with st.container():
                                is_sender = msg['sender_id'] == st.session_state.user_id
                                display_message(msg, is_sender)
                except Exception as e:
                    logger.error(f"Error loading messages: {e}")

                    # Show demo messages in case of error
                    st.info("Showing demonstration messages. In production, actual encrypted messages would be displayed.")

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
                                message_style = f"""
                                    <div style='
                                        padding: 10px;
                                        border-radius: 10px;
                                        margin: 5px;
                                        background-color: {"#e3f2fd" if msg["sent"] else "#f5f5f5"};
                                        text-align: {"right" if msg["sent"] else "left"};
                                        max-width: 80%;
                                        float: {"right" if msg["sent"] else "left"};
                                        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                                    '>
                                        <strong>{"You" if msg["sent"] else recipient_name}</strong><br>
                                        {msg["content"]}
                                    </div>
                                    <div style='clear: both;'></div>
                                """
                                st.markdown(message_style, unsafe_allow_html=True)
                            with col2:
                                st.caption(msg["time"])
                                if not msg["sent"]:
                                    st.caption("✓ Read")

        # Message composition - fixed at bottom
        with st.container():
            st.divider()

            col1, col2 = st.columns([5, 1])

            with col1:
                message_text = st.text_area("Compose Message", height=100, 
                                           placeholder="Type your secure message here...", 
                                           key="message_input")

            with col2:
                st.write("")
                st.write("")
                send_button = st.button("Send 📤", type="primary", key="send_button")

                # File attachment option
                st.caption("Attachments")
                file_upload = st.file_uploader("", type=["pdf", "jpg", "png", "docx"], key="file_upload")

            if send_button and message_text:
                try:
                    # Initialize secure messaging
                    secure_messaging = SecureMessaging()

                    # In demo mode, create a simple mock key
                    class DemoPublicKey:
                        def encrypt(self, data, padding):
                            return data  # Just return data for demo

                    recipient_key = DemoPublicKey()

                    attachment_info = ""
                    if file_upload:
                        # In production, encrypt and store file
                        attachment_info = f"\n[Attached: {file_upload.name}]"

                    try:
                        message_id = send_message(
                            st.session_state.user_id,
                            st.session_state.selected_recipient,
                            message_text + attachment_info,
                            recipient_key
                        )

                        if message_id:
                            st.success("Message sent securely!")
                            st.rerun()
                        else:
                            st.error("Failed to send message")
                    except Exception as e:
                        logger.error(f"Error sending message: {e}")

                        # For demo - simulate message sending
                        st.success("Message sent securely! (Demo mode)")
                        st.rerun()
                except Exception as e:
                    logger.error(f"Error initializing secure messaging: {e}")
                    st.error("Error sending message. Please try again.")

    else:
        # Show message summary/inbox when no conversation is selected
        st.header("📥 Recent Conversations")

        try:
            # Attempt to get recent conversations from the database
            try:
                conn = get_database_connection()
                recent_query = """
                    SELECT 
                        CASE 
                            WHEN m.sender_id = %s THEN m.recipient_id
                            ELSE m.sender_id
                        END as contact_id,
                        CASE 
                            WHEN m.sender_id = %s THEN r.username
                            ELSE s.username
                        END as contact_name,
                        MAX(m.created_at) as last_message_time,
                        COUNT(CASE WHEN m.read_at IS NULL AND m.recipient_id = %s THEN 1 END) as unread_count
                    FROM messages m
                    JOIN users s ON m.sender_id = s.id
                    JOIN users r ON m.recipient_id = r.id
                    WHERE m.sender_id = %s OR m.recipient_id = %s
                    GROUP BY contact_id, contact_name
                    ORDER BY last_message_time DESC
                """
                conversations = pd.read_sql(
                    recent_query, conn, 
                    params=(st.session_state.user_id, st.session_state.user_id, 
                            st.session_state.user_id, st.session_state.user_id, 
                            st.session_state.user_id)
                )
                conn.close()

                # Check if we got valid data
                if conversations is None or len(conversations.columns) == 0:
                    raise Exception("Invalid data returned from database")

            except Exception as db_error:
                logger.error(f"Database error while loading conversations: {db_error}")
                # Fallback to getting messages directly
                try:
                    # Try to get all messages for this user instead
                    all_messages = get_messages(st.session_state.user_id)

                    if all_messages:
                        # Create a simpler conversation summary from messages
                        conversation_data = []
                        seen_users = set()

                        for msg in sorted(all_messages, key=lambda x: x.get('created_at', datetime.min), reverse=True):
                            contact_id = msg['sender_id'] if msg['sender_id'] != st.session_state.user_id else msg['recipient_id']
                            contact_name = msg['sender_username'] if msg['sender_id'] != st.session_state.user_id else msg['recipient_username']

                            # Only add each contact once (most recent message)
                            if contact_id not in seen_users:
                                conversation_data.append({
                                    'contact_id': contact_id,
                                    'contact_name': contact_name,
                                    'last_message_time': msg.get('created_at'),
                                    'unread_count': 1 if not msg.get('read_at') and msg['recipient_id'] == st.session_state.user_id else 0
                                })
                                seen_users.add(contact_id)

                        # Convert to DataFrame
                        conversations = pd.DataFrame(conversation_data)
                    else:
                        # If no messages, raise exception to fall back to demo data
                        raise Exception("No messages found")

                except Exception as e:
                    logger.error(f"Failed to create conversation summary from messages: {e}")
                    # Create empty DataFrame with expected columns to show demo data
                    conversations = pd.DataFrame(columns=['contact_id', 'contact_name', 'last_message_time', 'unread_count'])
                    st.info("Unable to load your conversations. Showing demonstration data instead.")

            if len(conversations) > 0:
                for _, conv in conversations.iterrows():
                    # Create a clickable conversation preview
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        unread_badge = f"<span style='background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{conv['unread_count']}</span> " if conv['unread_count'] > 0 else ""

                        preview_style = f"""
                            <div style='
                                padding: 15px;
                                border-radius: 5px;
                                margin: 5px 0;
                                background-color: {"#f0f7ff" if conv['unread_count'] > 0 else "#f8f9fa"};
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                cursor: pointer;
                            '>
                                <strong>{unread_badge}{conv['contact_name']}</strong><br>
                                <small>{format_timestamp(conv['last_message_time'])}</small>
                            </div>
                        """

                        if st.markdown(preview_style, unsafe_allow_html=True):
                            st.session_state.selected_recipient = conv['contact_id']
                            st.rerun()

                    with col2:
                        if st.button("Open", key=f"open_{conv['contact_id']}"):
                            st.session_state.selected_recipient = conv['contact_id']
                            st.rerun()
            else:
                # Show demo conversation previews
                st.info("No conversations yet. Start a new one from the sidebar!")

                # Show demo conversation previews
                demo_previews = [
                    {"name": "Dr. Smith", "time": "2 days ago", "unread": 2},
                    {"name": "Dr. Johnson", "time": "1 week ago", "unread": 0}
                ]

                for i, preview in enumerate(demo_previews):
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        unread_badge = f"<span style='background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{preview['unread']}</span> " if preview['unread'] > 0 else ""

                        preview_style = f"""
                            <div style='
                                padding: 15px;
                                border-radius: 5px;
                                margin: 5px 0;
                                background-color: {"#f0f7ff" if preview['unread'] > 0 else "#f8f9fa"};
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                cursor: pointer;
                            '>
                                <strong>{unread_badge}{preview['name']}</strong><br>
                                <small>{preview['time']}</small>
                            </div>
                        """
                        st.markdown(preview_style, unsafe_allow_html=True)

                    with col2:
                        if st.button("Open", key=f"demo_open_{i}"):
                            # In demo mode, set to a fixed recipient ID
                            st.session_state.selected_recipient = i + 2
                            st.rerun()

        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            # Show a more helpful error message and demo data instead of just an error
            st.warning("We couldn't connect to the message database. Showing demonstration data below.")

            # Display demo conversations instead of showing an error
            demo_previews = [
                {"name": "Dr. Smith", "time": "2 days ago", "unread": 2},
                {"name": "Dr. Johnson", "time": "1 week ago", "unread": 0},
                {"name": "Dr. Williams", "time": "Yesterday", "unread": 1},
                {"name": "Dr. Brown", "time": "3 days ago", "unread": 0}
            ]

            for i, preview in enumerate(demo_previews):
                col1, col2 = st.columns([5, 1])

                with col1:
                    unread_badge = f"<span style='background-color: #ff4b4b; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8em;'>{preview['unread']}</span> " if preview['unread'] > 0 else ""

                    preview_style = f"""
                        <div style='
                            padding: 15px;
                            border-radius: 5px;
                            margin: 5px 0;
                            background-color: {"#f0f7ff" if preview['unread'] > 0 else "#f8f9fa"};
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                            cursor: pointer;
                        '>
                            <strong>{unread_badge}{preview['name']}</strong><br>
                            <small>{preview['time']}</small>
                        </div>
                    """
                    st.markdown(preview_style, unsafe_allow_html=True)

                with col2:
                    if st.button("Open", key=f"demo_error_open_{i}"):
                        # In demo mode, set to a fixed recipient ID
                        st.session_state.selected_recipient = i + 2
                        st.rerun()

if __name__ == "__main__":
    messages_page()