import streamlit as st
from database import get_database_connection
import pandas as pd

def project_management_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return

    st.title("Project Management")

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .project-section {
            background-color: #1E1E2F;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .form-section {
            background-color: #252525;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .project-card {
            border-left: 4px solid #6C63FF;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #252525;
            border-radius: 0.3rem;
            transition: transform 0.2s ease;
        }
        .project-card:hover {
            transform: translateY(-2px);
        }
        .collaborators-section {
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .metric-container {
            background-color: #1E1E2F;
            padding: 0.5rem;
            border-radius: 0.3rem;
            text-align: center;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #6C63FF;
        }
        .metric-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.7);
        }
    </style>
    """, unsafe_allow_html=True)

    # Project creation
    st.markdown('<div class="project-section">', unsafe_allow_html=True)
    with st.expander("Create New Project", expanded=False):
        st.markdown('<div class="form-section">', unsafe_allow_html=True)

        with st.form("create_project_form"):
            project_name = st.text_input("Project Name")
            project_description = st.text_area("Project Description")
            is_public = st.checkbox("Make project public", value=True, 
                                   help="Public projects can be discovered by other researchers")

            submitted = st.form_submit_button("Create Project")

            if submitted:
                try:
                    conn = get_database_connection()
                    cur = conn.cursor()

                    cur.execute("""
                        INSERT INTO projects (name, description, owner_id, is_public)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id;
                    """, (project_name, project_description, st.session_state.user_id, is_public))

                    project_id = cur.fetchone()[0]
                    conn.commit()
                    cur.close()
                    conn.close()

                    st.success(f"Project created successfully! Project ID: {project_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating project: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Project statistics
    try:
        conn = get_database_connection()
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

        stats_df = pd.read_sql(stats_query, conn, params=(st.session_state.user_id,))

        if not stats_df.empty:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                <div class="metric-container">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Total Projects</div>
                </div>
                """.format(stats_df.iloc[0]['project_count']), unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="metric-container">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Data Sets</div>
                </div>
                """.format(stats_df.iloc[0]['data_count']), unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="metric-container">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Collaborators</div>
                </div>
                """.format(stats_df.iloc[0]['collaborator_count']), unsafe_allow_html=True)

        conn.close()
    except Exception as e:
        st.error(f"Error loading project statistics: {str(e)}")

    # Project listing
    st.markdown('<div class="project-section">', unsafe_allow_html=True)
    st.subheader("Your Projects")
    try:
        conn = get_database_connection()
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

        df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()

        if len(df) > 0:
            for _, row in df.iterrows():
                st.markdown(f"""
                <div class="project-card">
                    <h3>{row['name']}</h3>
                    <p>{row['description']}</p>
                    <p><small>Created: {row['created_at'].strftime('%Y-%m-%d')} • {'Public' if row['is_public'] else 'Private'}</small></p>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Project Details"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Description:** {row['description']}")
                        st.write(f"**Created:** {row['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Visibility:** {'Public' if row['is_public'] else 'Private'}")

                    with col2:
                        st.metric("Data Sets", row['data_count'])
                        st.metric("Collaborators", row['collaborator_count'])

                    # Project actions
                    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

                    with action_col1:
                        if st.button("Add Data", key=f"add_data_{row['id']}"):
                            st.session_state.selected_project_id = row['id']
                            st.session_state.selected_project_name = row['name']
                            st.switch_page("pages/1_Data_Upload.py")

                    with action_col2:
                        if st.button("Export Data", key=f"export_{row['id']}"):
                            st.session_state.selected_project_id = row['id']
                            st.session_state.selected_project_name = row['name']
                            st.switch_page("pages/4_Data_Export.py")

                    with action_col3:
                        if st.button("Manage Collaborators", key=f"collab_{row['id']}"):
                            # Add collaborator management functionality here
                            st.info("Collaborator management coming soon")
        else:
            st.info("No projects found. Create a new project to get started.")

    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    project_management_page()