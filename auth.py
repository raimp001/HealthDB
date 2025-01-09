import hashlib
import secrets
from database import get_database_connection

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

def authenticate_user(username, password):
    """Authenticate user credentials."""
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
    
    if result and verify_password(result[1], password):
        return result[0]
    return None
