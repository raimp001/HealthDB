import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

def get_database_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")

def init_database():
    """Initialize database tables."""
    conn = get_database_connection()
    cur = conn.cursor()

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bio TEXT,
            institution VARCHAR(200),
            research_interests TEXT[]
        );
    """)

    # Create projects table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            owner_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_public BOOLEAN DEFAULT true
        );
    """)

    # Create research_data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_data (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES projects(id),
            data_type VARCHAR(50) NOT NULL,
            data_value JSONB,
            metadata JSONB,
            uploaded_by INTEGER REFERENCES users(id),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create badges table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            criteria TEXT,
            icon_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create user_badges table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            badge_id INTEGER REFERENCES badges(id),
            awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id)
        );
    """)

    # Create collaborations table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collaborations (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES projects(id),
            user_id INTEGER REFERENCES users(id),
            role VARCHAR(50) NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

def save_research_data(project_id, data_type, data_value, metadata, user_id):
    """Save research data to database."""
    conn = get_database_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO research_data (project_id, data_type, data_value, metadata, uploaded_by)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (project_id, data_type, data_value, metadata, user_id))
    
    data_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return data_id

def get_project_data(project_id):
    """Retrieve research data for a specific project."""
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT * FROM research_data
        WHERE project_id = %s
        ORDER BY uploaded_at DESC;
    """, (project_id,))
    
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_user_profile(user_id):
    """Get user profile with badges and collaborations."""
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get user basic info
    cur.execute("""
        SELECT id, username, email, bio, institution, research_interests, created_at
        FROM users
        WHERE id = %s;
    """, (user_id,))
    user_info = cur.fetchone()

    # Get user badges
    cur.execute("""
        SELECT b.name, b.description, b.icon_name, ub.awarded_at
        FROM user_badges ub
        JOIN badges b ON b.id = ub.badge_id
        WHERE ub.user_id = %s
        ORDER BY ub.awarded_at DESC;
    """, (user_id,))
    badges = cur.fetchall()

    # Get collaborations
    cur.execute("""
        SELECT p.name as project_name, c.role, c.joined_at
        FROM collaborations c
        JOIN projects p ON p.id = c.project_id
        WHERE c.user_id = %s
        ORDER BY c.joined_at DESC;
    """, (user_id,))
    collaborations = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "user_info": user_info,
        "badges": badges,
        "collaborations": collaborations
    }

def award_badge(user_id, badge_id):
    """Award a badge to a user."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO user_badges (user_id, badge_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, badge_id) DO NOTHING
            RETURNING id;
        """, (user_id, badge_id))

        badge_award_id = cur.fetchone()
        conn.commit()
        return badge_award_id is not None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def add_collaboration(project_id, user_id, role):
    """Add a user as collaborator to a project."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO collaborations (project_id, user_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, user_id) DO UPDATE
            SET role = EXCLUDED.role
            RETURNING id;
        """, (project_id, user_id, role))

        collab_id = cur.fetchone()[0]
        conn.commit()
        return collab_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()