import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from database import get_database_connection
import openai
import json
import networkx as nx

def generate_research_insights(data):
    """Generate research insights using OpenAI."""
    client = openai.OpenAI()
    
    try:
        prompt = f"""
        Analyze the following research data and identify key trends, connections, and emerging patterns:
        {json.dumps(data, indent=2)}
        
        Please provide:
        1. Main research clusters
        2. Emerging trends
        3. Potential collaboration opportunities
        4. Research impact analysis
        
        Format the response as JSON with these keys: clusters, trends, collaborations, impact
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a research trend analysis expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating insights: {str(e)}")
        return None

def create_network_graph(nodes, edges):
    """Create an interactive network graph using Plotly."""
    G = nx.Graph()
    
    # Add nodes and edges to the graph
    for node in nodes:
        G.add_node(node['id'], **node)
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
    
    # Calculate layout
    pos = nx.spring_layout(G)
    
    # Create traces for nodes
    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode='markers+text',
        hoverinfo='text',
        text=[G.nodes[node].get('label', '') for node in G.nodes()],
        marker=dict(
            size=20,
            color=[G.nodes[node].get('group', 0) for node in G.nodes()],
            colorscale='Viridis',
            showscale=True
        )
    )
    
    # Create traces for edges
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += (x0, x1, None)
        edge_trace['y'] += (y0, y1, None)
    
    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                   ))
    
    return fig

def get_research_data():
    """Get research data from database."""
    conn = get_database_connection()
    try:
        query = """
        WITH paper_connections AS (
            SELECT DISTINCT
                p1.id as source_id,
                p1.title as source_title,
                p2.id as target_id,
                p2.title as target_title,
                COUNT(DISTINCT c1.user_id) as connection_strength
            FROM research_papers p1
            JOIN collaborations c1 ON p1.project_id = c1.project_id
            JOIN collaborations c2 ON c1.project_id = c2.project_id
            JOIN research_papers p2 ON c2.project_id = p2.project_id
            WHERE p1.id != p2.id
            GROUP BY p1.id, p1.title, p2.id, p2.title
        )
        SELECT 
            source_id, source_title, 
            target_id, target_title,
            connection_strength
        FROM paper_connections
        ORDER BY connection_strength DESC
        LIMIT 100;
        """
        
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def research_trends_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access research trends.")
        return
    
    st.title("Research Trends Analysis")
    
    # Get research data
    data = get_research_data()
    
    if data.empty:
        st.info("No research data available for analysis.")
        return
    
    # Create nodes and edges for the network graph
    nodes = []
    edges = []
    
    # Process data for visualization
    unique_papers = pd.concat([
        data[['source_id', 'source_title']].rename(columns={'source_id': 'id', 'source_title': 'title'}),
        data[['target_id', 'target_title']].rename(columns={'target_id': 'id', 'target_title': 'title'})
    ]).drop_duplicates()
    
    for _, paper in unique_papers.iterrows():
        nodes.append({
            'id': paper['id'],
            'label': paper['title'],
            'group': 1
        })
    
    for _, row in data.iterrows():
        edges.append({
            'source': row['source_id'],
            'target': row['target_id'],
            'weight': row['connection_strength']
        })
    
    # Create network visualization
    st.subheader("Research Network Visualization")
    network_fig = create_network_graph(nodes, edges)
    st.plotly_chart(network_fig, use_container_width=True)
    
    # Generate and display AI insights
    st.subheader("AI-Generated Research Insights")
    with st.spinner("Analyzing research trends..."):
        insights = generate_research_insights({
            'papers': unique_papers.to_dict('records'),
            'connections': data.to_dict('records')
        })
        
        if insights:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Research Clusters")
                for cluster in insights['clusters']:
                    st.markdown(f"- {cluster}")
                    
                st.markdown("### Emerging Trends")
                for trend in insights['trends']:
                    st.markdown(f"- {trend}")
            
            with col2:
                st.markdown("### Collaboration Opportunities")
                for collab in insights['collaborations']:
                    st.markdown(f"- {collab}")
                    
                st.markdown("### Research Impact")
                for impact in insights['impact']:
                    st.markdown(f"- {impact}")

if __name__ == "__main__":
    research_trends_page()
