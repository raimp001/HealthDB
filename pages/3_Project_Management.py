import streamlit as st
from database import get_database_connection
import pandas as pd
from datetime import datetime
import logging
from components.navigation import render_navigation
from typing import Dict, List, Optional, Tuple, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Functions
def get_project_statistics(user_id: int) -> Dict[str, int]:
    """
    Fetch project statistics for the given user.

    Args:
        user_id: The ID of the user to retrieve statistics for.

    Returns:
        Dictionary with counts of projects, data sets, and collaborators.
    """
    try:
        with get_database_connection() as conn:
            stats_query = """
                SELECT 
                    COUNT(DISTINCT p.id) as project_count,
                    COUNT(DISTINCT rd.id) as data_count,
                    COUNT(DISTINCT c.user_id) as collaborator_count
                FROM projects p
                LEFT JOIN research_data rd ON p.id = rd.project_id
                LEFT JOIN collaborations c ON p.id = c.project_id
                WHERE p.owner_id = %s;
            """
            stats_df = pd.read_sql(stats_query, conn, params=(user_id,))
            if not stats_df.empty:
                return {
                    'project_count': int(stats_df.iloc[0]['project_count']),
                    'data_count': int(stats_df.iloc[0]['data_count']),
                    'collaborator_count': int(stats_df.iloc[0]['collaborator_count'])
                }
            return {'project_count': 0, 'data_count': 0, 'collaborator_count': 0}
    except Exception as e:
        logger.error(f"Error fetching project statistics: {e}")
        st.error("Failed to fetch project statistics. Please try again later.")
        return {'project_count': 0, 'data_count': 0, 'collaborator_count': 0}

def get_user_projects(user_id: int) -> pd.DataFrame:
    """
    Retrieve projects owned by the given user.

    Args:
        user_id: The ID of the user to fetch projects for.

    Returns:
        DataFrame containing project details.
    """
    try:
        with get_database_connection() as conn:
            query = """
                SELECT p.id, p.name, p.description, p.created_at, p.is_public,
                       COUNT(DISTINCT rd.id) as data_count,
                       COUNT(DISTINCT c.user_id) as collaborator_count
                FROM projects p
                LEFT JOIN research_data rd ON p.id = rd.project_id
                LEFT JOIN collaborations c ON p.id = c.project_id
                WHERE p.owner_id = %s
                GROUP BY p.id, p.name, p.description, p.created_at, p.is_public
                ORDER BY p.created_at DESC;
            """
            return pd.read_sql(query, conn, params=(user_id,))
    except Exception as e:
        logger.error(f"Error fetching user projects: {e}")
        st.error("Failed to load projects. Please check your connection and try again.")
        return pd.DataFrame(columns=[
            'id', 'name', 'description', 'created_at', 'is_public', 
            'data_count', 'collaborator_count'
        ])

def create_project(user_id: int, name: str, description: str, is_public: bool) -> Optional[int]:
    """
    Create a new project in the database.

    Args:
        user_id: The ID of the project owner.
        name: The project name.
        description: The project description.
        is_public: Whether the project is publicly visible.

    Returns:
        The new project ID if successful, None otherwise.
    """
    if not name.strip():
        st.warning("Project name cannot be empty.")
        return None
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (name, description, owner_id, is_public)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (name.strip(), description.strip(), user_id, is_public))
                project_id = cur.fetchone()[0]
                conn.commit()
                return project_id
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        st.error("Failed to create project. Please try again.")
        return None

def create_demo_projects(user_id: int) -> bool:
    """
    Populate the database with demo projects if the user has none.

    Args:
        user_id: The ID of the user to create demo projects for.

    Returns:
        True if successful or no action needed, False on error.
    """
    try:
        with get_database_connection() as conn:
            count_df = pd.read_sql("SELECT COUNT(*) FROM projects WHERE owner_id = %s", conn, params=(user_id,))
            if count_df.iloc[0][0] == 0:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'projects'
                        );
                    """)
                    if cur.fetchone()[0]:
                        cur.execute("""
                            INSERT INTO projects (name, description, owner_id, is_public, created_at)
                            VALUES 
                                ('Genomic Analysis', 'Analysis of genomic data for rare diseases', %s, true, NOW()),
                                ('Clinical Trial Data', 'Multi-center trial data repository', %s, true, NOW() - INTERVAL '2 days'),
                                ('COVID-19 Patient Outcomes', 'Tracking long-term outcomes for COVID-19 patients', %s, true, NOW() - INTERVAL '1 week'),
                                ('Brain Imaging Study', 'MRI analysis of neurological disorders', %s, false, NOW() - INTERVAL '1 month')
                            ON CONFLICT DO NOTHING
                            RETURNING id;
                        """, (user_id, user_id, user_id, user_id))
                        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating demo projects: {e}")
        return False

# UI Rendering Functions
def render_project_card(project: Dict[str, Any]) -> None:
    """
    Display a single project card with expandable details.

    Args:
        project: Dictionary containing project data.
    """
    created_at = pd.to_datetime(project.get('created_at', datetime.now()), errors='coerce') or datetime.now()
    date_str = created_at.strftime('%Y-%m-%d')
    datetime_str = created_at.strftime('%Y-%m-%d %H:%M')

    project_id = project.get('id', 0)
    name = project.get('name', 'Untitled Project')
    description = project.get('description', 'No description available')
    is_public = project.get('is_public', True)
    data_count = project.get('data_count', 0)
    collaborator_count = project.get('collaborator_count', 0)

    st.markdown(f"""
    <div class="project-card">
        <h3>{name}</h3>
        <p>{description[:100] + '...' if len(description) > 100 else description}</p>
        <p><small>Created: {date_str} • {'Public' if is_public else 'Private'}</small></p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Project Details"):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Description:** {description}")
            st.write(f"**Created:** {datetime_str}")
            st.write(f"**Visibility:** {'Public' if is_public else 'Private'}")
        with col2:
            st.metric("Data Sets", data_count)
            st.metric("Collaborators", collaborator_count)

        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("Add Data", key=f"add_data_{project_id}", help="Upload data to this project"):
                st.session_state.selected_project_id = project_id
                st.session_state.selected_project_name = name
                try:
                    st.switch_page("pages/1_Data_Upload.py")
                except:
                    st.info("Would navigate to Data Upload page in production")
        with action_col2:
            if st.button("Export Data", key=f"export_{project_id}", help="Export project data"):
                st.session_state.selected_project_id = project_id
                st.session_state.selected_project_name = name
                try:
                    st.switch_page("pages/4_Data_Export.py")
                except:
                    st.info("Would navigate to Data Export page in production")
        with action_col3:
            if st.button("Manage Collaborators", key=f"collab_{project_id}", help="Manage project collaborators"):
                st.session_state.selected_project_id = project_id
                st.session_state.selected_project_name = name
                st.info("Collaborator management module would open here")

def render_demo_projects() -> None:
    """Display hardcoded demo projects when no real data is available."""
    demo_projects = [
        {'id': 1, 'name': 'Genomic Analysis', 'description': 'Analysis of genomic data for rare diseases', 
         'created_at': datetime.now(), 'is_public': True, 'data_count': 3, 'collaborator_count': 2},
        {'id': 2, 'name': 'Clinical Trial Data', 'description': 'Multi-center trial data repository', 
         'created_at': datetime.now(), 'is_public': True, 'data_count': 5, 'collaborator_count': 4},
        {'id': 3, 'name': 'COVID-19 Patient Outcomes', 'description': 'Tracking long-term outcomes for COVID-19 patients', 
         'created_at': datetime.now(), 'is_public': True, 'data_count': 2, 'collaborator_count': 3},
        {'id': 4, 'name': 'Brain Imaging Study', 'description': 'MRI analysis of neurological disorders', 
         'created_at': datetime.now(), 'is_public': False, 'data_count': 7, 'collaborator_count': 1}
    ]
    for project in demo_projects:
        render_project_card(project)

def render_project_creation(user_id: int) -> None:
    """Render the project creation form."""
    st.markdown('<div class="project-section">', unsafe_allow_html=True)
    with st.expander("Create New Project", expanded=False):
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        with st.form("create_project_form"):
            project_name = st.text_input("Project Name", help="Enter a unique name for your project")
            project_description = st.text_area("Project Description", help="Describe your project's purpose")
            col1, col2 = st.columns(2)
            with col1:
                is_public = st.checkbox("Make project public", value=True, 
                                      help="Public projects can be discovered by other researchers")
            # with col2:
                # contains_phi = st.checkbox("Contains PHI/PII", value=False,
                #                            help="Project contains Protected Health Information or Personally Identifiable Information")
                # Note: PHI/PII status not implemented in database schema yet
            if st.form_submit_button("Create Project"):
                project_id = create_project(user_id, project_name, project_description, is_public)
                if project_id:
                    st.success(f"Project '{project_name}' created successfully!")
                    st.rerun()
                elif getattr(st.session_state, 'demo_mode', False):
                    st.success(f"Project '{project_name}' created successfully! (Demo Mode)")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_statistics(stats: Dict[str, int]) -> None:
    """Display project statistics in a three-column layout."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{stats['project_count']}</div>
            <div class="metric-label">Total Projects</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{stats['data_count']}</div>
            <div class="metric-label">Data Sets</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{stats['collaborator_count']}</div>
            <div class="metric-label">Collaborators</div>
        </div>
        """, unsafe_allow_html=True)

def render_project_list(projects_df: pd.DataFrame) -> None:
    """Render the project list with filters."""
    st.markdown('<div class="project-section">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_status = st.selectbox("Status", options=["All Projects", "Public Only", "Private Only"])
        with filter_col2:
            filter_sort = st.selectbox("Sort By", options=["Newest First", "Oldest First", "Name (A-Z)", "Name (Z-A)"])
        with filter_col3:
            filter_search = st.text_input("Search Projects", placeholder="Project name or description...")
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("Your Projects")
    if len(projects_df) > 0:
        filtered_df = projects_df.copy()
        if filter_status == "Public Only":
            filtered_df = filtered_df[filtered_df['is_public'] == True]
        elif filter_status == "Private Only":
            filtered_df = filtered_df[filtered_df['is_public'] == False]
        if filter_search:
            search_mask = (
                filtered_df['name'].str.contains(filter_search, case=False, na=False) |
                filtered_df['description'].str.contains(filter_search, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]
        if filter_sort == "Oldest First":
            filtered_df = filtered_df.sort_values('created_at', ascending=True)
        elif filter_sort == "Name (A-Z)":
            filtered_df = filtered_df.sort_values('name', ascending=True)
        elif filter_sort == "Name (Z-A)":
            filtered_df = filtered_df.sort_values('name', ascending=False)

        if len(filtered_df) > 0:
            for _, row in filtered_df.iterrows():
                render_project_card(row)
        else:
            st.info("No projects match your filters. Try adjusting your search criteria.")
    elif getattr(st.session_state, 'demo_mode', False):
        st.info("Showing demonstration projects.")
        render_demo_projects()
    else:
        st.info("No projects found. Create a new project to get started.")
    st.markdown('</div>', unsafe_allow_html=True)

def project_management_page():
    """Main function to render the project management page."""
    st.set_page_config(
        page_title="Research Project Management",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Demo mode setup
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.session_state.user_id = 1
        st.session_state.username = "Demo User"
        st.session_state.demo_mode = True
        st.markdown("""
        <div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
            <strong>Demo Mode:</strong> You are viewing sample data. No login required.
        </div>
        """, unsafe_allow_html=True)

    # Page setup
    render_navigation()
    st.title("📋 Project Management")
    st.markdown("""
    <style>
        .project-section {background-color: #f8f9fa; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,0,0,0.1);}
        .form-section {background-color: #ffffff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid rgba(0,0,0,0.05);}
        .project-card {border-left: 4px solid #6C63FF; padding: 1rem; margin-bottom: 1rem; background-color: #ffffff; border-radius: 0.3rem; transition: transform 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}
        .project-card:hover {transform: translateY(-2px);}
        .metric-container {background-color: #f8f9fa; padding: 0.5rem; border-radius: 0.3rem; text-align: center;}
        .metric-value {font-size: 1.5rem; font-weight: bold; color: #6C63FF;}
        .metric-label {font-size: 0.8rem; color: rgba(0,0,0,0.7);}
        .filter-container {padding: 10px; background-color: #f5f5f5; border-radius: 5px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

    # Render sections
    render_project_creation(st.session_state.user_id)
    with st.spinner("Loading statistics..."):
        stats = get_project_statistics(st.session_state.user_id)
        if stats['project_count'] == 0 and getattr(st.session_state, 'demo_mode', False):
            stats = {'project_count': 4, 'data_count': 17, 'collaborator_count': 8}
        render_statistics(stats)
    create_demo_projects(st.session_state.user_id)
    with st.spinner("Loading projects..."):
        projects_df = get_user_projects(st.session_state.user_id)
        render_project_list(projects_df)

if __name__ == "__main__":
    project_management_page()