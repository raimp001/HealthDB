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

    # Create institutions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS institutions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) UNIQUE NOT NULL,
            type VARCHAR(50),
            country VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create irb_submissions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS irb_submissions (
            id SERIAL PRIMARY KEY,
            title VARCHAR(300) NOT NULL,
            principal_investigator_id INTEGER REFERENCES users(id),
            institution_id INTEGER REFERENCES institutions(id),
            project_description TEXT NOT NULL,
            methodology TEXT NOT NULL,
            risks_and_benefits TEXT NOT NULL,
            participant_selection TEXT NOT NULL,
            consent_process TEXT NOT NULL,
            data_safety_plan TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create irb_reviews table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS irb_reviews (
            id SERIAL PRIMARY KEY,
            submission_id INTEGER REFERENCES irb_submissions(id),
            reviewer_id INTEGER REFERENCES users(id),
            review_type VARCHAR(50) NOT NULL,
            comments TEXT,
            decision VARCHAR(50),
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(submission_id, reviewer_id)
        );
    """)

    # Create irb_documents table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS irb_documents (
            id SERIAL PRIMARY KEY,
            submission_id INTEGER REFERENCES irb_submissions(id),
            document_type VARCHAR(100) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_by INTEGER REFERENCES users(id),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # Create researcher_messages table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS researcher_messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER REFERENCES users(id),
            recipient_id INTEGER REFERENCES users(id),
            encrypted_content TEXT NOT NULL,
            encrypted_key TEXT NOT NULL,
            iv TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            CONSTRAINT unique_message_id UNIQUE (id)
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_sender 
        ON researcher_messages(sender_id);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_recipient 
        ON researcher_messages(recipient_id);
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

def submit_irb_application(
    title: str,
    pi_id: int,
    institution_id: int,
    project_description: str,
    methodology: str,
    risks_and_benefits: str,
    participant_selection: str,
    consent_process: str,
    data_safety_plan: str
) -> int:
    """Submit a new IRB application."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO irb_submissions (
                title, principal_investigator_id, institution_id,
                project_description, methodology, risks_and_benefits,
                participant_selection, consent_process, data_safety_plan
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            title, pi_id, institution_id, project_description,
            methodology, risks_and_benefits, participant_selection,
            consent_process, data_safety_plan
        ))

        submission_id = cur.fetchone()[0]
        conn.commit()
        return submission_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_irb_submissions(institution_id: int = None, pi_id: int = None):
    """Get IRB submissions with optional filtering."""
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT 
            s.*,
            u.username as pi_name,
            i.name as institution_name,
            COUNT(DISTINCT r.id) as review_count
        FROM irb_submissions s
        JOIN users u ON s.principal_investigator_id = u.id
        JOIN institutions i ON s.institution_id = i.id
        LEFT JOIN irb_reviews r ON s.id = r.submission_id
    """

    conditions = []
    params = []

    if institution_id:
        conditions.append("s.institution_id = %s")
        params.append(institution_id)
    if pi_id:
        conditions.append("s.principal_investigator_id = %s")
        params.append(pi_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY s.id, u.username, i.name ORDER BY s.submitted_at DESC"

    try:
        cur.execute(query, params)
        submissions = cur.fetchall()
        return submissions
    finally:
        cur.close()
        conn.close()

def submit_irb_review(
    submission_id: int,
    reviewer_id: int,
    review_type: str,
    comments: str,
    decision: str
) -> int:
    """Submit a review for an IRB submission."""
    conn = get_database_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO irb_reviews (
                submission_id, reviewer_id, review_type,
                comments, decision
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (submission_id, reviewer_id)
            DO UPDATE SET
                review_type = EXCLUDED.review_type,
                comments = EXCLUDED.comments,
                decision = EXCLUDED.decision,
                reviewed_at = CURRENT_TIMESTAMP
            RETURNING id;
        """, (submission_id, reviewer_id, review_type, comments, decision))

        review_id = cur.fetchone()[0]

        # Update submission status based on review decision
        cur.execute("""
            UPDATE irb_submissions
            SET status = %s,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (decision, submission_id))

        conn.commit()
        return review_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()