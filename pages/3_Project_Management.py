import streamlit as st
from database import get_database_connection
import pandas as pd
from datetime import datetime
import logging
from components.navigation import render_navigation
from typing import Dict, List, Optional, Tuple, Any
import time

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
                    COUNT(DISTINCT c.user_id) as collaborator_count,
                    COUNT(DISTINCT CASE WHEN p.created_at > NOW() - INTERVAL '30 days' THEN p.id END) as recent_projects
                FROM projects p
                LEFT JOIN research_data rd ON p.id = rd.project_id
                LEFT JOIN collaborations c ON p.id = c.project_id
                WHERE p.owner_id = %s AND p.archived = FALSE;
            """
            stats_df = pd.read_sql(stats_query, conn, params=(user_id,))
            if not stats_df.empty:
                return {
                    'project_count': int(stats_df.iloc[0]['project_count']),
                    'data_count': int(stats_df.iloc[0]['data_count']),
                    'collaborator_count': int(stats_df.iloc[0]['collaborator_count']),
                    'recent_projects': int(stats_df.iloc[0]['recent_projects'])
                }
            return {'project_count': 0, 'data_count': 0, 'collaborator_count': 0, 'recent_projects': 0}
    except Exception as e:
        logger.error(f"Error fetching project statistics: {e}")
        st.error("Failed to fetch project statistics. Please try again later.")
        return {'project_count': 0, 'data_count': 0, 'collaborator_count': 0, 'recent_projects': 0}

def get_user_projects(user_id: int, include_archived: bool = False) -> pd.DataFrame:
    """
    Retrieve projects owned by the given user.

    Args:
        user_id: The ID of the user to fetch projects for.
        include_archived: Whether to include archived projects.

    Returns:
        DataFrame containing project details.
    """
    try:
        with get_database_connection() as conn:
            query = """
                SELECT p.id, p.name, p.description, p.created_at, p.updated_at, p.is_public, p.archived,
                       COALESCE(p.tags, '') as tags,
                       COUNT(DISTINCT rd.id) as data_count,
                       COUNT(DISTINCT c.user_id) as collaborator_count,
                       (SELECT MAX(a.timestamp) FROM activity_log a WHERE a.project_id = p.id) as last_activity
                FROM projects p
                LEFT JOIN research_data rd ON p.id = rd.project_id
                LEFT JOIN collaborations c ON p.id = c.project_id
                WHERE p.owner_id = %s
                """ + ("" if include_archived else " AND p.archived = FALSE") + """
                GROUP BY p.id, p.name, p.description, p.created_at, p.updated_at, p.is_public, p.archived, p.tags
                ORDER BY p.created_at DESC;
            """
            return pd.read_sql(query, conn, params=(user_id,))
    except Exception as e:
        logger.error(f"Error fetching user projects: {e}")
        st.error("Failed to load projects. Please check your connection and try again.")
        return pd.DataFrame(columns=[
            'id', 'name', 'description', 'created_at', 'updated_at', 'is_public', 'archived', 
            'tags', 'data_count', 'collaborator_count', 'last_activity'
        ])

def create_project(user_id: int, name: str, description: str, is_public: bool, tags: str = "") -> Optional[int]:
    """
    Create a new project in the database.

    Args:
        user_id: The ID of the project owner.
        name: The project name.
        description: The project description.
        is_public: Whether the project is publicly visible.
        tags: Comma-separated list of project tags.

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
                    INSERT INTO projects (name, description, owner_id, is_public, tags, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id;
                """, (name.strip(), description.strip(), user_id, is_public, tags.strip()))
                project_id = cur.fetchone()[0]
                conn.commit()

                # Log the activity
                cur.execute("""
                    INSERT INTO activity_log (user_id, project_id, action, timestamp)
                    VALUES (%s, %s, %s, NOW());
                """, (user_id, project_id, "Project created"))
                conn.commit()

                return project_id
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        st.error("Failed to create project. Please try again.")
        return None

def update_project(project_id: int, user_id: int, name: str, description: str, is_public: bool, tags: str = "") -> bool:
    """
    Update an existing project.

    Args:
        project_id: The ID of the project to update.
        user_id: The ID of the user making the update.
        name: The updated project name.
        description: The updated project description.
        is_public: The updated public visibility setting.
        tags: Updated comma-separated list of project tags.

    Returns:
        True if successful, False otherwise.
    """
    if not name.strip():
        st.warning("Project name cannot be empty.")
        return False
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE projects 
                    SET name = %s, description = %s, is_public = %s, tags = %s, updated_at = NOW()
                    WHERE id = %s AND owner_id = %s;
                """, (name.strip(), description.strip(), is_public, tags.strip(), project_id, user_id))

                if cur.rowcount > 0:
                    # Log the activity
                    cur.execute("""
                        INSERT INTO activity_log (user_id, project_id, action, timestamp)
                        VALUES (%s, %s, %s, NOW());
                    """, (user_id, project_id, "Project updated"))
                    conn.commit()
                    return True
                else:
                    return False
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        st.error("Failed to update project. Please try again.")
        return False

def toggle_project_archive(project_id: int, user_id: int, archive: bool) -> bool:
    """
    Archive or unarchive a project.

    Args:
        project_id: The ID of the project to update.
        user_id: The ID of the user making the update.
        archive: True to archive, False to unarchive.

    Returns:
        True if successful, False otherwise.
    """
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE projects 
                    SET archived = %s, updated_at = NOW()
                    WHERE id = %s AND owner_id = %s
                    RETURNING name;
                """, (archive, project_id, user_id))

                result = cur.fetchone()
                if result:
                    project_name = result[0]
                    action = "Project archived" if archive else "Project restored"

                    # Log the activity
                    cur.execute("""
                        INSERT INTO activity_log (user_id, project_id, action, timestamp)
                        VALUES (%s, %s, %s, NOW());
                    """, (user_id, project_id, action))
                    conn.commit()
                    return True
                else:
                    return False
    except Exception as e:
        logger.error(f"Error {'archiving' if archive else 'unarchiving'} project: {e}")
        st.error(f"Failed to {'archive' if archive else 'unarchive'} project. Please try again.")
        return False

def duplicate_project(project_id: int, user_id: int) -> Optional[int]:
    """
    Create a duplicate of an existing project.

    Args:
        project_id: The ID of the project to duplicate.
        user_id: The ID of the user making the duplicate.

    Returns:
        The new project ID if successful, None otherwise.
    """
    try:
        with get_database_connection() as conn:
            # First get the project details
            project_df = pd.read_sql("""
                SELECT name, description, is_public, tags
                FROM projects
                WHERE id = %s AND owner_id = %s;
            """, conn, params=(project_id, user_id))

            if project_df.empty:
                return None

            project = project_df.iloc[0]

            # Create new project with 'Copy of' prefix
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (name, description, owner_id, is_public, tags, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id;
                """, (f"Copy of {project['name']}", project['description'], user_id, 
                      project['is_public'], project['tags']))

                new_project_id = cur.fetchone()[0]

                # Log the activity
                cur.execute("""
                    INSERT INTO activity_log (user_id, project_id, action, timestamp)
                    VALUES (%s, %s, %s, NOW());
                """, (user_id, new_project_id, f"Project duplicated from {project_id}"))
                conn.commit()

                return new_project_id
    except Exception as e:
        logger.error(f"Error duplicating project: {e}")
        st.error("Failed to duplicate project. Please try again.")
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
                            INSERT INTO projects (name, description, owner_id, is_public, created_at, updated_at, tags)
                            VALUES 
                                ('Genomic Analysis', 'Analysis of genomic data for rare diseases', %s, true, NOW(), NOW(), 'genomics,research,disease'),
                                ('Clinical Trial Data', 'Multi-center trial data repository', %s, true, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', 'clinical,trial,medical'),
                                ('COVID-19 Patient Outcomes', 'Tracking long-term outcomes for COVID-19 patients', %s, true, NOW() - INTERVAL '1 week', NOW() - INTERVAL '1 week', 'covid,patients,longitudinal'),
                                ('Brain Imaging Study', 'MRI analysis of neurological disorders', %s, false, NOW() - INTERVAL '1 month', NOW() - INTERVAL '1 month', 'neurology,imaging,mri')
                            ON CONFLICT DO NOTHING
                            RETURNING id;
                        """, (user_id, user_id, user_id, user_id))

                        # Create activity log entries for demo projects
                        for project_id in cur.fetchall():
                            cur.execute("""
                                INSERT INTO activity_log (user_id, project_id, action, timestamp)
                                VALUES (%s, %s, %s, NOW() - (random() * INTERVAL '10 days'));
                            """, (user_id, project_id[0], "Project created"))

                        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating demo projects: {e}")
        return False

# UI Rendering Functions
def render_project_card(project: Dict[str, Any], view_mode: str) -> None:
    """
    Display a single project card with expandable details.

    Args:
        project: Dictionary containing project data.
        view_mode: Either 'list' or 'grid' to control layout.
    """
    created_at = pd.to_datetime(project.get('created_at', datetime.now()), errors='coerce') or datetime.now()
    updated_at = pd.to_datetime(project.get('updated_at', datetime.now()), errors='coerce') or datetime.now()
    date_str = created_at.strftime('%Y-%m-%d')
    datetime_str = created_at.strftime('%Y-%m-%d %H:%M')
    updated_str = updated_at.strftime('%Y-%m-%d %H:%M')

    last_activity = pd.to_datetime(project.get('last_activity'), errors='coerce')
    activity_str = last_activity.strftime('%Y-%m-%d %H:%M') if pd.notnull(last_activity) else "Never"

    project_id = project.get('id', 0)
    name = project.get('name', 'Untitled Project')
    description = project.get('description', 'No description available')
    is_public = project.get('is_public', True)
    archived = project.get('archived', False)
    data_count = project.get('data_count', 0)
    collaborator_count = project.get('collaborator_count', 0)
    tags = project.get('tags', '').split(',') if project.get('tags') else []

    # Card styling based on archived status
    card_style = "archived-card" if archived else "project-card"

    if view_mode == 'grid':
        col = st.column_config.Column(width="medium")
        with st.container():
            st.markdown(f"""
            <div class="{card_style}">
                <h3>{name}</h3>
                <p class="card-description">{description[:100] + '...' if len(description) > 100 else description}</p>
                <div class="tag-container">
                    {"".join([f'<span class="tag">{tag.strip()}</span>' for tag in tags if tag.strip()])}
                </div>
                <p><small>Created: {date_str} • {'Public' if is_public else 'Private'} {' • Archived' if archived else ''}</small></p>
                <div class="card-metrics">
                    <span class="metric"><i class="fas fa-database"></i> {data_count} Datasets</span>
                    <span class="metric"><i class="fas fa-users"></i> {collaborator_count} Collaborators</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:  # list view
        st.markdown(f"""
        <div class="{card_style}">
            <h3>{name}</h3>
            <p>{description[:150] + '...' if len(description) > 150 else description}</p>
            <div class="tag-container">
                {"".join([f'<span class="tag">{tag.strip()}</span>' for tag in tags if tag.strip()])}
            </div>
            <p><small>Created: {date_str} • Last Updated: {updated_str} • {'Public' if is_public else 'Private'} {' • Archived' if archived else ''}</small></p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("Project Details"):
        tab1, tab2 = st.tabs(["Overview", "Actions"])

        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Description:** {description}")
                st.write(f"**Created:** {datetime_str}")
                st.write(f"**Last Updated:** {updated_str}")
                st.write(f"**Last Activity:** {activity_str}")
                st.write(f"**Visibility:** {'Public' if is_public else 'Private'}")
                if archived:
                    st.write("**Status:** Archived")
                if tags:
                    st.write("**Tags:** " + ", ".join([tag.strip() for tag in tags if tag.strip()]))
            with col2:
                st.metric("Data Sets", data_count)
                st.metric("Collaborators", collaborator_count)

                # Add progress metrics if available
                if 'progress' in project:
                    st.progress(project.get('progress', 0)/100, text=f"Progress: {project.get('progress', 0)}%")

        with tab2:
            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button("Add Data", key=f"add_data_{project_id}", help="Upload data to this project"):
                    st.session_state.selected_project_id = project_id
                    st.session_state.selected_project_name = name
                    try:
                        st.switch_page("pages/1_Data_Upload.py")
                    except:
                        st.info("Would navigate to Data Upload page in production")

                if st.button("Duplicate", key=f"duplicate_{project_id}", help="Create a copy of this project"):
                    if duplicate_project(project_id, st.session_state.user_id):
                        st.success(f"Project '{name}' has been duplicated!")
                        time.sleep(1)
                        st.rerun()
                    elif getattr(st.session_state, 'demo_mode', False):
                        st.success(f"Project '{name}' has been duplicated! (Demo Mode)")
                        time.sleep(1)
                        st.rerun()

                edit_btn = st.button("Edit Project", key=f"edit_{project_id}", help="Edit project details")
                if edit_btn:
                    st.session_state.editing_project = project_id
                    st.session_state.editing_project_data = project
                    st.rerun()

            with action_col2:
                if st.button("Export Data", key=f"export_{project_id}", help="Export project data"):
                    st.session_state.selected_project_id = project_id
                    st.session_state.selected_project_name = name
                    try:
                        st.switch_page("pages/4_Data_Export.py")
                    except:
                        st.info("Would navigate to Data Export page in production")

                if st.button("Manage Collaborators", key=f"collab_{project_id}", help="Manage project collaborators"):
                    st.session_state.selected_project_id = project_id
                    st.session_state.selected_project_name = name
                    st.info("Collaborator management module would open here")

                if archived:
                    if st.button("Restore Project", key=f"restore_{project_id}", 
                               help="Restore this project from archived status", type="primary"):
                        if toggle_project_archive(project_id, st.session_state.user_id, False):
                            st.success(f"Project '{name}' has been restored!")
                            time.sleep(1)
                            st.rerun()
                        elif getattr(st.session_state, 'demo_mode', False):
                            st.success(f"Project '{name}' has been restored! (Demo Mode)")
                            time.sleep(1)
                            st.rerun()
                else:
                    if st.button("Archive Project", key=f"archive_{project_id}", 
                               help="Archive this project", type="secondary"):
                        if toggle_project_archive(project_id, st.session_state.user_id, True):
                            st.success(f"Project '{name}' has been archived!")
                            time.sleep(1)
                            st.rerun()
                        elif getattr(st.session_state, 'demo_mode', False):
                            st.success(f"Project '{name}' has been archived! (Demo Mode)")
                            time.sleep(1)
                            st.rerun()

def render_demo_projects(view_mode: str) -> None:
    """
    Display hardcoded demo projects when no real data is available.

    Args:
        view_mode: Either 'list' or 'grid' to control layout.
    """
    demo_projects = [
        {'id': 1, 'name': 'Genomic Analysis', 'description': 'Analysis of genomic data for rare diseases', 
         'created_at': datetime.now(), 'updated_at': datetime.now(), 'is_public': True, 'data_count': 3, 
         'collaborator_count': 2, 'tags': 'genomics,research,disease', 'progress': 65},
        {'id': 2, 'name': 'Clinical Trial Data', 'description': 'Multi-center trial data repository', 
         'created_at': datetime.now(), 'updated_at': datetime.now(), 'is_public': True, 'data_count': 5, 
         'collaborator_count': 4, 'tags': 'clinical,trial,medical', 'progress': 80},
        {'id': 3, 'name': 'COVID-19 Patient Outcomes', 'description': 'Tracking long-term outcomes for COVID-19 patients', 
         'created_at': datetime.now(), 'updated_at': datetime.now(), 'is_public': True, 'data_count': 2, 
         'collaborator_count': 3, 'tags': 'covid,patients,longitudinal', 'progress': 45},
        {'id': 4, 'name': 'Brain Imaging Study', 'description': 'MRI analysis of neurological disorders', 
         'created_at': datetime.now(), 'updated_at': datetime.now(), 'is_public': False, 'data_count': 7, 
         'collaborator_count': 1, 'tags': 'neurology,imaging,mri', 'progress': 30}
    ]

    if view_mode == 'grid':
        cols = st.columns(2)
        for i, project in enumerate(demo_projects):
            with cols[i % 2]:
                render_project_card(project, view_mode)
    else:
        for project in demo_projects:
            render_project_card(project, view_mode)

def render_project_creation_or_editing(user_id: int) -> None:
    """Render the project creation or editing form."""
    editing_mode = 'editing_project' in st.session_state
    project_data = st.session_state.get('editing_project_data', {}) if editing_mode else {}

    form_title = "Edit Project" if editing_mode else "Create New Project"
    button_text = "Update Project" if editing_mode else "Create Project"

    st.markdown('<div class="project-section">', unsafe_allow_html=True)
    with st.expander(form_title, expanded=editing_mode):
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        with st.form(f"{'edit' if editing_mode else 'create'}_project_form"):
            project_name = st.text_input("Project Name", 
                                      value=project_data.get('name', '') if editing_mode else "",
                                      help="Enter a unique name for your project")

            project_description = st.text_area("Project Description", 
                                            value=project_data.get('description', '') if editing_mode else "",
                                            help="Describe your project's purpose")

            project_tags = st.text_input("Tags (comma separated)", 
                                      value=project_data.get('tags', '') if editing_mode else "",
                                      help="Add relevant tags to categorize your project")

            col1, col2 = st.columns(2)
            with col1:
                is_public = st.checkbox("Make project public", 
                                      value=project_data.get('is_public', True) if editing_mode else True, 
                                      help="Public projects can be discovered by other researchers")

            if st.form_submit_button(button_text):
                if editing_mode:
                    success = update_project(
                        st.session_state.editing_project, 
                        user_id, 
                        project_name, 
                        project_description, 
                        is_public,
                        project_tags
                    )
                    if success:
                        st.success(f"Project '{project_name}' updated successfully!")
                        # Clear editing state
                        if 'editing_project' in st.session_state:
                            del st.session_state.editing_project
                        if 'editing_project_data' in st.session_state:
                            del st.session_state.editing_project_data
                        time.sleep(1)
                        st.rerun()
                    elif getattr(st.session_state, 'demo_mode', False):
                        st.success(f"Project '{project_name}' updated successfully! (Demo Mode)")
                        if 'editing_project' in st.session_state:
                            del st.session_state.editing_project
                        if 'editing_project_data' in st.session_state:
                            del st.session_state.editing_project_data
                        time.sleep(1)
                        st.rerun()
                else:
                    project_id = create_project(user_id, project_name, project_description, is_public, project_tags)
                    if project_id:
                        st.success(f"Project '{project_name}' created successfully!")
                        time.sleep(1)
                        st.rerun()
                    elif getattr(st.session_state, 'demo_mode', False):
                        st.success(f"Project '{project_name}' created successfully! (Demo Mode)")
                        time.sleep(1)
                        st.rerun()

        if editing_mode:
            if st.button("Cancel Editing", key="cancel_edit"):
                if 'editing_project' in st.session_state:
                    del st.session_state.editing_project
                if 'editing_project_data' in st.session_state:
                    del st.session_state.editing_project_data
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_statistics(stats: Dict[str, int]) -> None:
    """Display project statistics with improved visualizations."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{stats['project_count']}</div>
            <div class="metric-label">Total Projects</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-icon">📂</div>
            <div class="metric-value">{stats['data_count']}</div>
            <div class="metric-label">Data Sets</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{stats['collaborator_count']}</div>
            <div class="metric-label">Collaborators</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-container recent-metric">
            <div class="metric-icon">🆕</div>
            <div class="metric-value">{stats.get('recent_projects', 0)}</div>
            <div class="metric-label">New in Last 30 Days</div>
        </div>
        """, unsafe_allow_html=True)

def render_project_list(projects_df: pd.DataFrame) -> None:
    """Render the project list with improved filters and view options."""
    st.markdown('<div class="project-section">', unsafe_allow_html=True)

    # View controls at the top
    view_controls_col1, view_controls_col2 = st.columns([1, 4])
    with view_controls_col1:
        view_mode = st.radio("View", ["List", "Grid"], horizontal=True, 
                           help="Choose how to display your projects")
    with view_controls_col2:
        st.write("")  # Placeholder for alignment

    # More advanced filtering options
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
        with filter_col1:
            filter_status = st.selectbox("Status", options=["Active Projects", "All Projects", "Public Only", "Private Only", "Archived"])
        with filter_col2:
            filter_sort = st.selectbox("Sort By", options=["Newest First", "Oldest First", "Name (A-Z)", "Name (Z-A)", 
                                                       "Most Datasets", "Most Collaborators", "Recently Updated"])
        with filter_col3:
            if 'tags' in projects_df.columns and not projects_df.empty:
                all_tags = []
                for tags_str in projects_df['tags'].dropna():
                    all_tags.extend([tag.strip() for tag in tags_str.split(',') if tag.strip()])
                unique_tags = sorted(set(all_tags))
                filter_tag = st.selectbox("Filter by Tag", options=["All Tags"] + unique_tags)
            else:
                filter_tag = "All Tags"
        with filter_col4:
            filter_search = st.text_input("Search", placeholder="Project name or description...")
        st.markdown('</div>', unsafe_allow_html=True)

    # Projects header with counts
    include_archived = filter_status == "Archived" or filter_status == "All Projects"
    active_count = len(projects_df[~projects_df.get('archived', False)]) if 'archived' in projects_df.columns else len(projects_df)
    archived_count = len(projects_df[projects_df.get('archived', False)]) if 'archived' in projects_df.columns else 0

    # Project counts header
    st.markdown(f"""
    <div class="section-header">
        <h2>Your Projects</h2>
        <div class="count-badges">
            <span class="badge active-badge">{active_count} Active</span>
            {f'<span class="badge archived-badge">{archived_count} Archived</span>' if archived_count > 0 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display projects based on filters
    if len(projects_df) > 0:
        filtered_df = projects_df.copy()

        # Filter by status
        if filter_status == "Active Projects":
            filtered_df = filtered_df[~filtered_df.get('archived', False)]
        elif filter_status == "Public Only":
            filtered_df = filtered_df[filtered_df['is_public'] == True]
            if 'archived' in filtered_df.columns:
                filtered_df = filtered_df[~filtered_df['archived']]
        elif filter_status == "Private Only":
            filtered_df = filtered_df[filtered_df['is_public'] == False]
            if 'archived' in filtered_df.columns:
                filtered_df = filtered_df[~filtered_df['archived']]
        elif filter_status == "Archived":
            if 'archived' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['archived']]

        # Filter by tag
        if filter_tag != "All Tags" and 'tags' in filtered_df.columns:
            tag_mask = filtered_df['tags'].apply(lambda x: filter_tag in [tag.strip() for tag in str(x).split(',')] if pd.notnull(x) else False)
            filtered_df = filtered_df[tag_mask]

        # Filter by search term
        if filter_search:
            search_mask = (
                filtered_df['name'].str.contains(filter_search, case=False, na=False) |
                filtered_df['description'].str.contains(filter_search, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]

        # Sort projects
        if filter_sort == "Oldest First":
            filtered_df = filtered_df.sort_values('created_at', ascending=True)
        elif filter_sort == "Name (A-Z)":
            filtered_df = filtered_df.sort_values('name', ascending=True)
        elif filter_sort == "Name (Z-A)":
            filtered_df = filtered_df.sort_values('name', ascending=False)
        elif filter_sort == "Most Datasets":
            filtered_df = filtered_df.sort_values('data_count', ascending=False)
        elif filter_sort == "Most Collaborators":
            filtered_df = filtered_df.sort_values('collaborator_count', ascending=False)
        elif filter_sort == "Recently Updated":
            if 'updated_at' in filtered_df.columns:
                filtered_df = filtered_df.sort_values('updated_at', ascending=False)
            else:
                filtered_df = filtered_df.sort_values('created_at', ascending=False)
        else:  # Default to newest first
            filtered_df = filtered_df.sort_values('created_at', ascending=False)

        if len(filtered_df) > 0:
            # Display projects in grid or list view
            if view_mode.lower() == 'grid':
                cols = st.columns(2)
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    with cols[i % 2]:
                        render_project_card(row, 'grid')
            else:
                for _, row in filtered_df.iterrows():
                    render_project_card(row, 'list')
        else:
            st.info("No projects match your filters. Try adjusting your search criteria.")

            # Offer quick actions when no projects match
            st.markdown("""
            <div class="empty-state">
                <h3>Can't find what you're looking for?</h3>
                <p>Try adjusting your filters or create a new project.</p>
            </div>
            """, unsafe_allow_html=True)

    elif getattr(st.session_state, 'demo_mode', False):
        st.info("Showing demonstration projects.")
        render_demo_projects(view_mode.lower())
    else:
        # Empty state with helpful guidance
        st.markdown("""
        <div class="empty-state">
            <h3>No projects yet</h3>
            <p>Create your first project to get started. Projects help you organize your research data and collaborate with others.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Getting Started

        Projects are containers for your research data, analyses, and collaborations. Here's how to begin:

        1. Click "Create New Project" above
        2. Give your project a name and description
        3. Choose visibility settings
        4. Add datasets and invite collaborators

        Need help? Check out our [documentation](https://example.com/docs) or [contact support](mailto:support@example.com).
        """)

    # Pagination controls (simplified for demo)
    if len(projects_df) > 10:
        st.markdown('<div class="pagination-controls">', unsafe_allow_html=True)
        pag_col1, pag_col2, pag_col3 = st.columns([1, 3, 1])
        with pag_col1:
            st.button("← Previous", disabled=True)
        with pag_col2:
            st.write("Page 1 of 1")
        with pag_col3:
            st.button("Next →", disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
        <div class="demo-banner">
            <span class="demo-icon">🧪</span>
            <strong>Demo Mode:</strong> You are viewing sample data. No login required.
        </div>
        """, unsafe_allow_html=True)

    # Page setup
    render_navigation()
    st.title("📋 Project Management")
    st.markdown("""
    <style>
        /* General improvements */
        .project-section {background-color: #f8f9fa; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,0,0,0.1); transition: all 0.3s ease;}
        .form-section {background-color: #ffffff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid rgba(0,0,0,0.05);}

        /* Project cards */
        .project-card {border-left: 4px solid #6C63FF; padding: 1rem; margin-bottom: 1rem; background-color: #ffffff; border-radius: 0.3rem; transition: transform 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}
        .project-card:hover {transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
        .archived-card {border-left: 4px solid #6c757d; padding: 1rem; margin-bottom: 1rem; background-color: #f8f9fa; border-radius: 0.3rem; transition: transform 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.1); opacity: 0.8;}
        .archived-card:hover {transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);}

        /* Card content */
        .card-description {margin-bottom: 0.5rem; color: #495057;}
        .card-metrics {display: flex; justify-content: space-between; margin-top: 0.5rem;}
        .metric {font-size: 0.8rem; color: #6c757d;}

        /* Tags */
        .tag-container {margin: 0.5rem 0;}
        .tag {background-color: #e9ecef; color: #495057; padding: 0.2rem 0.5rem; border-radius: 1rem; font-size: 0.7rem; margin-right: 0.3rem; display: inline-block;}

        /* Statistics */
        .metric-container {background-color: #ffffff; padding: 1rem; border-radius: 0.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%; transition: transform 0.2s ease;}
        .metric-container:hover {transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
        .metric-icon {font-size: 1.5rem; margin-bottom: 0.3rem;}
        .metric-value {font-size: 2rem; font-weight: bold; color: #6C63FF; margin-bottom: 0.2rem;}
        .metric-label {font-size: 0.8rem; color: rgba(0,0,0,0.7);}
        .recent-metric .metric-value {color: #28a745;}

        /* Filters and controls */
        .filter-container {padding: 1rem; background-color: #f5f5f5; border-radius: 0.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05) inset;}
        .section-header {display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;}
        .count-badges {display: flex; gap: 0.5rem;}
        .badge {padding: 0.3rem 0.6rem; border-radius: 1rem; font-size: 0.8rem;}
        .active-badge {background-color: #e9ecef; color: #212529;}
        .archived-badge {background-color: #6c757d; color: white;}

        /* Empty states */
        .empty-state {text-align: center; padding: 2rem; background-color: #ffffff; border-radius: 0.5rem; margin: 1rem 0;}

        /* Pagination */
        .pagination-controls {display: flex; justify-content: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e9ecef;}

        /* Demo banner */
        .demo-banner {background-color: #cff4fc; color: #055160; padding: 0.5rem 1rem; border-radius: 0.3rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;}
        .demo-icon {font-size: 1.2rem;}
    </style>
    """, unsafe_allow_html=True)

    # Render page content
    tab1, tab2 = st.tabs(["Projects", "Templates"])

    with tab1:
        # Render project creation form
        render_project_creation_or_editing(st.session_state.user_id)

        # Render statistics with animation
        with st.spinner("Loading statistics..."):
            stats = get_project_statistics(st.session_state.user_id)
            if stats['project_count'] == 0 and getattr(st.session_state, 'demo_mode', False):
                stats = {'project_count': 4, 'data_count': 17, 'collaborator_count': 8, 'recent_projects': 2}
            render_statistics(stats)

        # Create demo projects if needed
        create_demo_projects(st.session_state.user_id)

        # Render project list with improved filtering
        with st.spinner("Loading projects..."):
            projects_df = get_user_projects(st.session_state.user_id, include_archived=True)
            render_project_list(projects_df)

    with tab2:
        st.markdown("""
        ### Project Templates

        Templates help you quickly start new projects with predefined structures.
        """)

        template_col1, template_col2 = st.columns(2)

        with template_col1:
            st.markdown("""
            <div class="project-card">
                <h3>Clinical Trial Template</h3>
                <p>Standard structure for clinical trial data management</p>
                <div class="tag-container">
                    <span class="tag">clinical</span>
                    <span class="tag">trial</span>
                    <span class="tag">medical</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Template Details"):
                st.write("**Description:** Pre-configured project structure for clinical trial data including patient demographics, outcomes, and regulatory documentation.")
                if st.button("Use Template", key="use_clinical"):
                    st.success("New project created from Clinical Trial Template!")

        with template_col2:
            st.markdown("""
            <div class="project-card">
                <h3>Genomic Research Template</h3>
                <p>Structure for genomic sequencing and analysis</p>
                <div class="tag-container">
                    <span class="tag">genomics</span>
                    <span class="tag">sequencing</span>
                    <span class="tag">bioinformatics</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Template Details"):
                st.write("**Description:** Ready-to-use structure for genomic research with sections for raw sequences, processed data, and analysis pipelines.")
                if st.button("Use Template", key="use_genomic"):
                    st.success("New project created from Genomic Research Template!")

if __name__ == "__main__":
    project_management_page()