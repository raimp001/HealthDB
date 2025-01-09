import streamlit as st
from database import (
    save_notification_preferences,
    get_user_notification_preferences,
    get_user_notifications,
    mark_notification_as_read
)
from utils.notification_service import notification_service
import openai
import json

def notification_center_page():
    """Notification center page for managing preferences and viewing notifications."""
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access the notification center.")
        return

    st.title("Notification Center")

    # Create tabs for notifications, preferences, and research tracking
    tab1, tab2, tab3 = st.tabs(["Notifications", "Research Topics", "Notification Settings"])

    with tab1:
        st.subheader("Your Notifications")
        notifications = get_user_notifications(st.session_state.user_id)

        if not notifications:
            st.info("No notifications yet!")
        else:
            for notif in notifications:
                with st.container():
                    col1, col2 = st.columns([5,1])
                    with col1:
                        st.markdown(
                            f"""<div style='
                                background-color: {'#F5F5F5' if notif['read'] else '#E3E3E3'};
                                padding: 1rem;
                                border-radius: 4px;
                                border-left: 3px solid {'#121212' if notif['read'] else '#C4F652'};
                                margin-bottom: 0.5rem;
                            '>
                            <strong>{notif['title']}</strong><br>
                            {notif['content']}<br>
                            <small>{notif['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    with col2:
                        if not notif['read']:
                            if st.button("Mark Read", key=f"read_{notif['id']}"):
                                if mark_notification_as_read(notif['id'], st.session_state.user_id):
                                    st.rerun()

    with tab2:
        st.subheader("Research Topic Tracking")

        # Add new research topic
        with st.form("add_research_topic"):
            col1, col2 = st.columns([3, 1])
            with col1:
                topic = st.text_input(
                    "Research Topic",
                    help="Enter a research topic you want to track"
                )
            with col2:
                frequency = st.selectbox(
                    "Update Frequency",
                    options=['daily', 'weekly', 'monthly'],
                    help="How often do you want updates?"
                )

            notification_channels = st.multiselect(
                "Notification Channels",
                options=['in_app', 'sms'],
                default=['in_app'],
                help="Choose how you want to receive notifications"
            )

            if st.form_submit_button("Track Topic"):
                if topic:
                    try:
                        # Get initial research insight using OpenAI
                        client = openai.OpenAI()
                        prompt = f"""Analyze current research trends in {topic} and provide a brief summary.
                        Focus on: 1) Recent developments 2) Key researchers 3) Future directions
                        Keep it concise and informative."""

                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are a research trend analyst."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=300
                        )

                        initial_insight = response.choices[0].message.content

                        # Save preferences and send initial notification
                        if save_notification_preferences(
                            st.session_state.user_id,
                            topic,
                            frequency
                        ):
                            notification_service.send_notification(
                                user_id=st.session_state.user_id,
                                title=f"Research Track: {topic}",
                                content=f"Initial Research Insight:\n{initial_insight}",
                                notification_type="research_update",
                                channels=notification_channels
                            )
                            st.success(f"Now tracking research in: {topic}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error setting up research tracking: {str(e)}")
                else:
                    st.error("Please enter a topic")

        # Display current research topics
        st.subheader("Topics You're Tracking")
        preferences = get_user_notification_preferences(st.session_state.user_id)

        if not preferences:
            st.info("You're not tracking any research topics yet")
        else:
            for pref in preferences:
                st.markdown(
                    f"""<div style='
                        background-color: #F5F5F5;
                        padding: 1rem;
                        border-radius: 4px;
                        border-left: 3px solid #C4F652;
                        margin-bottom: 0.5rem;
                    '>
                    <strong>{pref['topic']}</strong><br>
                    Updates: {pref['frequency']}<br>
                    Status: {'Active' if pref['enabled'] else 'Paused'}
                    </div>""",
                    unsafe_allow_html=True
                )

    with tab3:
        st.subheader("Notification Settings")

        # Global notification settings
        st.write("##### Global Settings")

        notification_enabled = st.toggle(
            "Enable All Notifications",
            value=True,
            help="Toggle all notifications on/off"
        )

        if notification_enabled:
            st.write("##### Channel Settings")

            # SMS notifications setup
            sms_enabled = st.checkbox("Enable SMS Notifications")
            if sms_enabled:
                phone = st.text_input(
                    "Phone Number",
                    help="Enter your phone number to receive SMS notifications"
                )
                if st.button("Verify Phone Number"):
                    if phone:
                        # TODO: Implement phone verification
                        st.success("Phone number saved")
                    else:
                        st.error("Please enter a phone number")

            # Email digest settings
            st.write("##### Email Digest Settings")
            email_digest = st.selectbox(
                "Research Digest Email",
                options=['Never', 'Daily', 'Weekly', 'Monthly'],
                help="Choose how often to receive email summaries"
            )

            if st.button("Save Settings"):
                st.success("Notification settings updated!")

if __name__ == "__main__":
    notification_center_page()