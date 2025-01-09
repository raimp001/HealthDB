from typing import Optional, Dict, Any
from twilio.rest import Client
import os
from database import create_notification, get_database_connection
import json
from datetime import datetime

class NotificationService:
    def __init__(self):
        self.twilio_client = Client(
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN')
        )
        self.twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')

    def send_sms_notification(self, phone_number: str, message: str) -> bool:
        """Send SMS notification using Twilio."""
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone_number
            )
            return True
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False

    def send_notification(self, 
                         user_id: int, 
                         title: str, 
                         content: str, 
                         notification_type: str,
                         channels: list = ['in_app']) -> bool:
        """Send notification through specified channels."""
        try:
            # Create notification record
            notification_id = create_notification(
                user_id=user_id,
                title=title,
                content=content,
                notification_type=notification_type
            )

            # Get user contact information
            conn = get_database_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT phone_number, email 
                FROM users 
                WHERE id = %s;
            """, (user_id,))
            user_info = cur.fetchone()
            
            success = True
            if 'sms' in channels and user_info[0]:  # Check if phone number exists
                sms_success = self.send_sms_notification(
                    user_info[0],
                    f"{title}\n\n{content}"
                )
                success = success and sms_success

            # Update sent_at timestamp
            if success:
                cur.execute("""
                    UPDATE notifications 
                    SET sent_at = CURRENT_TIMESTAMP 
                    WHERE id = %s;
                """, (notification_id,))
                conn.commit()

            cur.close()
            conn.close()
            return success

        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
            return False

    def get_research_updates(self, topic: str) -> list:
        """Get research updates for a specific topic."""
        try:
            # For demonstration, we'll return some mock updates
            # In production, this would integrate with research databases or APIs
            updates = [
                {
                    "title": f"New Research in {topic}",
                    "content": f"Recent developments in {topic} show promising results...",
                    "type": "research_update"
                }
            ]
            return updates
        except Exception as e:
            print(f"Failed to get research updates: {str(e)}")
            return []

notification_service = NotificationService()
