from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from datetime import datetime
from database import get_database_connection
from typing import List, Dict, Optional

class SecureMessaging:
    def __init__(self):
        self.key_size = 2048
        self.encoding = 'utf-8'

    def generate_key_pair(self) -> tuple:
        """Generate a new RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def encrypt_message(self, message: str, recipient_public_key: rsa.RSAPublicKey) -> Dict[str, str]:
        """Encrypt a message using recipient's public key."""
        # Generate a random symmetric key for this message
        symmetric_key = Fernet.generate_key()
        f = Fernet(symmetric_key)

        # Encrypt the message using the symmetric key
        encrypted_message = f.encrypt(message.encode(self.encoding))

        # Encrypt the symmetric key using recipient's public key
        encrypted_key = recipient_public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return {
            'encrypted_content': base64.b64encode(encrypted_message).decode(self.encoding),
            'encrypted_key': base64.b64encode(encrypted_key).decode(self.encoding),
            'iv': base64.b64encode(os.urandom(16)).decode(self.encoding)
        }

    def decrypt_message(self, encrypted_data: Dict[str, str], private_key: rsa.RSAPrivateKey) -> str:
        """Decrypt a message using recipient's private key."""
        try:
            # Decode the encrypted components
            encrypted_message = base64.b64decode(encrypted_data['encrypted_content'].encode(self.encoding))
            encrypted_key = base64.b64decode(encrypted_data['encrypted_key'].encode(self.encoding))

            # Decrypt the symmetric key
            symmetric_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Use the symmetric key to decrypt the message
            f = Fernet(symmetric_key)
            decrypted_message = f.decrypt(encrypted_message)
            return decrypted_message.decode(self.encoding)
        except Exception as e:
            raise Exception(f"Failed to decrypt message: {str(e)}")

def send_message(sender_id: int, recipient_id: int, message: str, recipient_public_key) -> int:
    """Send an encrypted message to another researcher."""
    try:
        secure_messaging = SecureMessaging()

        # Convert stored public key string back to key object
        # In production, implement proper key serialization/deserialization
        recipient_key = recipient_public_key  # Placeholder for key reconstruction

        # Encrypt the message
        encrypted_data = secure_messaging.encrypt_message(message, recipient_key)

        conn = get_database_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO researcher_messages 
            (sender_id, recipient_id, encrypted_content, encrypted_key, iv)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            sender_id, 
            recipient_id,
            encrypted_data['encrypted_content'],
            encrypted_data['encrypted_key'],
            encrypted_data['iv']
        ))

        message_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return message_id
    except Exception as e:
        raise Exception(f"Failed to send message: {str(e)}")

def get_messages(user_id: int, conversation_with: Optional[int] = None) -> List[Dict]:
    """Get messages for a user, optionally filtered by conversation partner."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        if conversation_with:
            cur.execute("""
                SELECT m.*, 
                       s.username as sender_username,
                       r.username as recipient_username
                FROM researcher_messages m
                JOIN users s ON s.id = m.sender_id
                JOIN users r ON r.id = m.recipient_id
                WHERE (m.sender_id = %s AND m.recipient_id = %s)
                   OR (m.sender_id = %s AND m.recipient_id = %s)
                ORDER BY m.created_at DESC;
            """, (user_id, conversation_with, conversation_with, user_id))
        else:
            cur.execute("""
                SELECT m.*, 
                       s.username as sender_username,
                       r.username as recipient_username
                FROM researcher_messages m
                JOIN users s ON s.id = m.sender_id
                JOIN users r ON r.id = m.recipient_id
                WHERE m.sender_id = %s OR m.recipient_id = %s
                ORDER BY m.created_at DESC;
            """, (user_id, user_id))

        messages = cur.fetchall()

        # Convert to list of dictionaries
        message_list = []
        for msg in messages:
            message_dict = {
                'id': msg[0],
                'sender_id': msg[1],
                'recipient_id': msg[2],
                'encrypted_content': msg[3],
                'encrypted_key': msg[4],
                'iv': msg[5],
                'created_at': msg[6],
                'read_at': msg[7],
                'sender_username': msg[8],
                'recipient_username': msg[9]
            }
            message_list.append(message_dict)

        return message_list
    finally:
        cur.close()
        conn.close()

def mark_message_as_read(message_id: int, user_id: int) -> bool:
    """Mark a message as read by the recipient."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE researcher_messages
            SET read_at = CURRENT_TIMESTAMP
            WHERE id = %s AND recipient_id = %s AND read_at IS NULL
            RETURNING id;
        """, (message_id, user_id))

        updated = cur.fetchone() is not None
        conn.commit()
        return updated
    finally:
        cur.close()
        conn.close()