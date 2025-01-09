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
    base64url_to_bytes,
    bytes_to_base64url,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorAttachment,
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
        """Generate options for passkey registration with biometric requirement."""
        options = generate_registration_options(
            rp_name=self.rp_name,
            rp_id=self.rp_id,
            user_id=str(user_id),
            user_name=username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,  # Prefer platform authenticator
                user_verification=UserVerificationRequirement.REQUIRED,  # Require biometric verification
                require_resident_key=True  # Enable passwordless authentication
            ),
        )
        return options

    def store_passkey_credential(self, user_id, verification_data):
        """Store passkey credential in database."""
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            credential_id = bytes_to_base64url(verification_data.credential_data.credential_id)
            public_key = bytes_to_base64url(verification_data.credential_data.public_key)

            cur.execute("""
                INSERT INTO passkey_credentials 
                (user_id, credential_id, public_key, sign_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (credential_id) 
                DO UPDATE SET sign_count = EXCLUDED.sign_count;
            """, (user_id, credential_id, public_key, verification_data.sign_count))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def get_user_credentials(self, user_id):
        """Get user's registered passkey credentials."""
        conn = get_database_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT credential_id, public_key, sign_count
                FROM passkey_credentials
                WHERE user_id = %s;
            """, (user_id,))

            credentials = []
            for cred_id, pub_key, sign_count in cur.fetchall():
                credentials.append({
                    'id': base64url_to_bytes(cred_id),
                    'public_key': base64url_to_bytes(pub_key),
                    'sign_count': sign_count,
                })
            return credentials
        finally:
            cur.close()
            conn.close()

    def verify_passkey_registration(self, user_id, options, response):
        """Verify passkey registration response and store credential."""
        try:
            verification = verify_registration_response(
                credential=response,
                expected_challenge=options.challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
            )

            # Store the verified credential
            self.store_passkey_credential(user_id, verification)
            return True
        except Exception as e:
            raise Exception(f"Passkey registration failed: {str(e)}")

    def generate_passkey_auth_options(self, user_id):
        """Generate options for passkey authentication with existing credentials."""
        credentials = self.get_user_credentials(user_id)

        return generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=[
                PublicKeyCredentialDescriptor(id=cred['id'])
                for cred in credentials
            ],
            user_verification=UserVerificationRequirement.REQUIRED,
        )

    def verify_passkey_auth(self, user_id, credential, options):
        """Verify passkey authentication with stored credentials."""
        try:
            credentials = self.get_user_credentials(user_id)
            if not credentials:
                return False

            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=options.challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                credential_public_key=credentials[0]['public_key'],
                credential_current_sign_count=credentials[0]['sign_count'],
            )

            # Update sign count
            self.store_passkey_credential(user_id, verification)
            return True
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
        """Verify face against stored encoding with enhanced error handling."""
        try:
            conn = get_database_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT face_encoding 
                FROM users 
                WHERE id = %s
            """, (user_id,))

            result = cur.fetchone()
            if not result or not result[0]:
                return False

            stored_encoding = np.frombuffer(
                base64.b64decode(result[0]), dtype=np.float64
            )

            # Get face encoding from current image
            face_locations = face_recognition.face_locations(face_image)
            if not face_locations:
                raise Exception("No face detected in the image")

            new_encoding = face_recognition.face_encodings(face_image, face_locations)[0]

            # Compare face encodings with stricter threshold
            matches = face_recognition.compare_faces([stored_encoding], new_encoding, tolerance=0.5)
            return matches[0]
        except Exception as e:
            raise Exception(f"Face verification failed: {str(e)}")
        finally:
            cur.close()
            conn.close()

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

def authenticate_user(user_id=None, username=None, password=None, face_image=None, passkey_response=None):
    """Enhanced multi-factor authentication handler."""
    if not user_id and not username:
        return None

    conn = get_database_connection()
    cur = conn.cursor()

    try:
        if username:
            cur.execute("""
                SELECT id, password_hash
                FROM users
                WHERE username = %s;
            """, (username,))
            result = cur.fetchone()
            if not result:
                return None
            user_id = result[0]

        auth_manager = AuthenticationManager()

        # Passkey authentication
        if passkey_response:
            try:
                if auth_manager.verify_passkey_auth(user_id, passkey_response, auth_manager.generate_passkey_auth_options(user_id)):
                    return user_id
            except Exception:
                return None

        # Face recognition
        if face_image is not None:
            try:
                if auth_manager.verify_face(user_id, face_image):
                    return user_id
            except Exception:
                return None

        # Password authentication (fallback)
        if password and result:
            if verify_password(result[1], password):
                return user_id

        return None
    finally:
        cur.close()
        conn.close()

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