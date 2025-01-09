import streamlit as st
import plotly.graph_objects as go
from database import get_user_profile, get_database_connection
import pandas as pd
import plotly.express as px
from datetime import datetime

def create_network_graph(user_id):
    """Create a network visualization of collaborations."""
    conn = get_database_connection()
    
    # Get all collaborations involving the user
    query = """
        WITH user_projects AS (
            SELECT DISTINCT project_id
            FROM collaborations
            WHERE user_id = %s
        )
        SELECT 
            u.username,
            p.name as project_name,
            c.role
        FROM collaborations c
        JOIN users u ON u.id = c.user_id
        JOIN projects p ON p.id = c.project_id
        WHERE c.project_id IN (SELECT project_id FROM user_projects)
    """
    
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    
    if len(df) == 0:
        return None
        
    # Create network graph
    fig = go.Figure()
    
    # Add nodes for users and projects
    users = df['username'].unique()
    projects = df['project_name'].unique()
    
    # Create positions for nodes
    user_positions = {user: (i, 1) for i, user in enumerate(users)}
    project_positions = {proj: (i, 0) for i, proj in enumerate(projects)}
    
    # Add edges (connections)
    edge_x = []
    edge_y = []
    for _, row in df.iterrows():
        x0, y0 = user_positions[row['username']]
        x1, y1 = project_positions[row['project_name']]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    ))
    
    # Add user nodes
    fig.add_trace(go.Scatter(
        x=[pos[0] for pos in user_positions.values()],
        y=[pos[1] for pos in user_positions.values()],
        mode='markers+text',
        marker=dict(size=20, color='#1f77b4'),
        text=list(user_positions.keys()),
        textposition='top center',
        name='Researchers'
    ))
    
    # Add project nodes
    fig.add_trace(go.Scatter(
        x=[pos[0] for pos in project_positions.values()],
        y=[pos[1] for pos in project_positions.values()],
        mode='markers+text',
        marker=dict(size=15, color='#2ca02c'),
        text=list(project_positions.keys()),
        textposition='bottom center',
        name='Projects'
    ))
    
    fig.update_layout(
        showlegend=True,
        hovermode='closest',
        title='Collaboration Network',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    return fig

def display_badge(badge):
    """Display a badge with its details."""
    with st.container():
        col1, col2 = st.columns([1, 4])
        with col1:
            # Display badge icon (using emoji as placeholder)
            st.markdown(f"### {badge['icon_name'] or '🏅'}")
        with col2:
            st.markdown(f"**{badge['name']}**")
            st.write(badge['description'])
            st.caption(f"Awarded: {badge['awarded_at'].strftime('%Y-%m-%d')}")

def researcher_profile_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Researcher Profile")
    
    # Get user profile data
    profile_data = get_user_profile(st.session_state.user_id)
    
    if not profile_data['user_info']:
        st.error("User profile not found.")
        return
    
    # Profile header
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(profile_data['user_info']['username'])
        if profile_data['user_info']['bio']:
            st.write(profile_data['user_info']['bio'])
        if profile_data['user_info']['institution']:
            st.write(f"🏛️ {profile_data['user_info']['institution']}")
        if profile_data['user_info']['research_interests']:
            st.write("Research Interests:")
            for interest in profile_data['user_info']['research_interests']:
                st.markdown(f"- {interest}")
    
    with col2:
        # Profile stats
        st.metric("Projects", len(profile_data['collaborations']))
        st.metric("Badges", len(profile_data['badges']))
    
    # Badges section
    st.header("Badges")
    if profile_data['badges']:
        for badge in profile_data['badges']:
            display_badge(badge)
    else:
        st.info("No badges earned yet. Start collaborating and contributing to earn badges!")
    
    # Collaboration Network
    st.header("Collaboration Network")
    network_fig = create_network_graph(st.session_state.user_id)
    if network_fig:
        st.plotly_chart(network_fig, use_container_width=True)
    else:
        st.info("Start collaborating with other researchers to build your network!")
    
    # Recent Activity
    st.header("Recent Collaborations")
    if profile_data['collaborations']:
        for collab in profile_data['collaborations']:
            with st.container():
                st.markdown(f"**{collab['project_name']}**")
                st.caption(f"Role: {collab['role']}")
                st.caption(f"Joined: {collab['joined_at'].strftime('%Y-%m-%d')}")
                st.markdown("---")
    else:
        st.info("No recent collaborations. Join a project to get started!")

if __name__ == "__main__":
    researcher_profile_page()
