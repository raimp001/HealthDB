import streamlit as st
from database import (
    save_notification_preferences,
    get_user_notification_preferences,
    get_user_notifications,
    mark_notification_as_read
)
from utils.notification_service import notification_service

def notification_center_page():
    """Notification center page for managing preferences and viewing notifications."""
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access the notification center.")
        return

    st.title("NOTIFICATION CENTER")

    # Create tabs for notifications and preferences
    tab1, tab2 = st.tabs(["Notifications", "Preferences"])

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
        st.subheader("Notification Preferences")
        
        # Add new preference
        with st.form("add_preference"):
            topic = st.text_input(
                "Research Topic",
                help="Enter a research topic you want to follow"
            )
            frequency = st.selectbox(
                "Update Frequency",
                options=['daily', 'weekly', 'monthly'],
                help="How often do you want to receive updates?"
            )
            
            if st.form_submit_button("Add Topic"):
                if topic:
                    if save_notification_preferences(
                        st.session_state.user_id,
                        topic,
                        frequency
                    ):
                        st.success(f"Added {topic} to your notification preferences!")
                        st.rerun()
                else:
                    st.error("Please enter a topic")

        # Display current preferences
        st.subheader("Current Preferences")
        preferences = get_user_notification_preferences(st.session_state.user_id)
        
        if not preferences:
            st.info("No notification preferences set")
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
                    Frequency: {pref['frequency']}<br>
                    Status: {'Active' if pref['enabled'] else 'Disabled'}
                    </div>""",
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    notification_center_page()
