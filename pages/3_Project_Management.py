import streamlit as st
from database import get_database_connection
import pandas as pd

def project_management_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Project Management")
    
    # Project creation
    with st.expander("Create New Project"):
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        
        if st.button("Create Project"):
            try:
                conn = get_database_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO projects (name, description, owner_id)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (project_name, project_description, st.session_state.user_id))
                
                project_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                conn.close()
                
                st.success(f"Project created successfully! Project ID: {project_id}")
            except Exception as e:
                st.error(f"Error creating project: {str(e)}")
    
    # Project listing
    st.subheader("Your Projects")
    try:
        conn = get_database_connection()
        query = """
            SELECT p.id, p.name, p.description, p.created_at,
                   COUNT(rd.id) as data_count
            FROM projects p
            LEFT JOIN research_data rd ON p.id = rd.project_id
            WHERE p.owner_id = %s
            GROUP BY p.id, p.name, p.description, p.created_at
            ORDER BY p.created_at DESC;
        """
        
        df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()
        
        if len(df) > 0:
            for _, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {row['name']}")
                        st.write(f"Description: {row['description']}")
                        st.write(f"Created: {row['created_at']}")
                    
                    with col2:
                        st.metric("Data Sets", row['data_count'])
                    
                    st.markdown("---")
        else:
            st.info("No projects found. Create a new project to get started.")
            
    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")

if __name__ == "__main__":
    project_management_page()
