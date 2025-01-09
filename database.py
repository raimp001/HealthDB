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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create projects table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            owner_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
