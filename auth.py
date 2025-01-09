import hashlib
import secrets
from database import get_database_connection
from zpass_interface import ZPassInterface, ZKProof

# Initialize ZPass interface
zpass = ZPassInterface()

def hash_password(password):
    """Hash password using SHA-256."""
    salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt

def verify_password(stored_password, provided_password):
    """Verify password hash."""
    hash_val, salt = stored_password.split(':')
    return hash_val == hashlib.sha256((provided_password + salt).encode()).hexdigest()

def create_user(username, password, email):
    """Create new user in the database."""
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
        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def authenticate_user(username, password, use_zkp=False):
    """Authenticate user credentials with optional ZKP support."""
    conn = get_database_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, password_hash
        FROM users
        WHERE username = %s;
    """, (username,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        return None

    user_id, password_hash = result

    if use_zkp:
        # Generate and verify ZKP for password-less authentication
        proof = zpass.generate_authentication_proof(str(user_id))
        if zpass.verify_authentication_proof(str(user_id), proof):
            return user_id
    else:
        # Traditional password verification
        if verify_password(password_hash, password):
            return user_id

    return None

def verify_data_integrity(data):
    """Generate and verify ZKP for data integrity."""
    proof = zpass.generate_data_proof(data)
    # TODO: Implement actual verification logic using zPass SDK
    return True