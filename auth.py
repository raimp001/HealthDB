import hashlib
import secrets
from database import get_database_connection
from zpass_interface import ZPassInterface, ZKProof
import face_recognition
import numpy as np
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
)
import base64
import json

# Initialize interfaces
zpass = ZPassInterface()

class AuthenticationManager:
    def __init__(self):
        self.rp_name = "Research Data Platform"
        self.rp_id = "localhost"  # In production, use actual domain
        self.origin = "https://localhost"

    def generate_passkey_registration_options(self, user_id, username):
        """Generate options for passkey registration."""
        options = generate_registration_options(
            rp_name=self.rp_name,
            rp_id=self.rp_id,
            user_id=str(user_id),
            user_name=username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.REQUIRED
            ),
        )
        return options

    def verify_passkey_registration(self, options, response):
        """Verify passkey registration response."""
        try:
            verification = verify_registration_response(
                credential=response,
                expected_challenge=options.challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
            )
            return verification
        except Exception as e:
            raise Exception(f"Passkey registration failed: {str(e)}")

    def generate_passkey_auth_options(self):
        """Generate options for passkey authentication."""
        return generate_authentication_options(
            rp_id=self.rp_id,
            user_verification=UserVerificationRequirement.REQUIRED,
        )

    def verify_passkey_auth(self, credential, options):
        """Verify passkey authentication."""
        try:
            return verify_authentication_response(
                credential=credential,
                expected_challenge=options.challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
            )
        except Exception as e:
            raise Exception(f"Passkey authentication failed: {str(e)}")

    def store_face_encoding(self, user_id, face_image):
        """Store face encoding in the database."""
        try:
            # Convert image to face encoding
            face_encoding = face_recognition.face_encodings(face_image)[0]
            encoded_data = base64.b64encode(face_encoding.tobytes()).decode('utf-8')

            conn = get_database_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE users 
                SET face_encoding = %s
                WHERE id = %s
            """, (encoded_data, user_id))

            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Failed to store face encoding: {str(e)}")

    def verify_face(self, user_id, face_image):
        """Verify face against stored encoding."""
        try:
            conn = get_database_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT face_encoding 
                FROM users 
                WHERE id = %s
            """, (user_id,))

            result = cur.fetchone()
            cur.close()
            conn.close()

            if not result or not result[0]:
                return False

            stored_encoding = np.frombuffer(
                base64.b64decode(result[0]), dtype=np.float64
            )

            # Get face encoding from current image
            new_encoding = face_recognition.face_encodings(face_image)[0]

            # Compare face encodings
            matches = face_recognition.compare_faces([stored_encoding], new_encoding)
            return matches[0]
        except Exception as e:
            raise Exception(f"Face verification failed: {str(e)}")

def create_user(username, password, email, face_image=None):
    """Create new user with optional face recognition."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        password_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (username, password_hash, email)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (username, password_hash, email))

        user_id = cur.fetchone()[0]

        # Store face encoding if provided
        if face_image is not None:
            auth_manager = AuthenticationManager()
            auth_manager.store_face_encoding(user_id, face_image)

        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def authenticate_user(username, password=None, face_image=None, passkey_response=None, use_zkp=False):
    """Multi-factor authentication handler."""
    conn = get_database_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, password_hash, face_encoding
        FROM users
        WHERE username = %s;
    """, (username,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        return None

    user_id, password_hash, stored_face = result

    # Passkey authentication
    if passkey_response:
        auth_manager = AuthenticationManager()
        try:
            if auth_manager.verify_passkey_auth(passkey_response, stored_passkey_options):
                return user_id
        except:
            return None

    # Face recognition
    if face_image is not None:
        auth_manager = AuthenticationManager()
        try:
            if auth_manager.verify_face(user_id, face_image):
                return user_id
        except:
            return None

    # ZKP authentication
    if use_zkp:
        proof = zpass.generate_authentication_proof(str(user_id))
        if zpass.verify_authentication_proof(str(user_id), proof):
            return user_id

    # Password authentication
    if password and verify_password(password_hash, password):
        return user_id

    return None

def hash_password(password):
    """Hash password using SHA-256."""
    salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt

def verify_password(stored_password, provided_password):
    """Verify password hash."""
    hash_val, salt = stored_password.split(':')
    return hash_val == hashlib.sha256((provided_password + salt).encode()).hexdigest()

def verify_data_integrity(data):
    """Generate and verify ZKP for data integrity."""
    proof = zpass.generate_data_proof(data)
    # TODO: Implement actual verification logic using zPass SDK
    return True