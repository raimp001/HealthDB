import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import openai
from typing import Dict, List, Any
import json

def generate_research_trends(research_area: str) -> Dict[str, Any]:
    """Generate research trends analysis using OpenAI."""
    try:
        client = openai.OpenAI()
        prompt = f"""Analyze current research trends in {research_area}.
        Return the response as a JSON object with the following structure:
        {{
            "main_topics": [{"name": "topic_name", "weight": float}],
            "connections": [{"source": "topic_a", "target": "topic_b", "strength": float}]
        }}
        Where weight represents topic importance (0-1) and strength represents connection strength (0-1).
        Include 5-8 main topics and their relevant connections."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a research trends analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating research trends: {str(e)}")
        return {"main_topics": [], "connections": []}

def create_network_graph(trends_data: Dict[str, Any]):
    """Create interactive network graph visualization using NetworkX and Plotly."""
    G = nx.Graph()

    # Add nodes with weights
    for topic in trends_data["main_topics"]:
        G.add_node(topic["name"], weight=topic["weight"])

    # Add edges with weights
    for conn in trends_data["connections"]:
        G.add_edge(conn["source"], conn["target"], weight=conn["strength"])

    # Calculate layout
    pos = nx.spring_layout(G, k=1, iterations=50)

    # Create node trace
    node_x = []
    node_y = []
    node_sizes = []
    node_text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        weight = G.nodes[node].get("weight", 0.5)
        node_sizes.append(weight * 50)
        node_text.append(f"{node}<br>Importance: {weight:.2f}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=list(G.nodes()),
        textposition="top center",
        marker=dict(
            size=node_sizes,
            color='#C4F652',  # Lime from Aleo
            line=dict(color='#121212', width=1)  # Coal from Aleo
        ),
        hovertext=node_text,
        hoverinfo='text'
    )

    # Create edge trace
    edge_x = []
    edge_y = []
    edge_text = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        weight = G.edges[edge].get("weight", 0.5)
        edge_text.append(f"Connection strength: {weight:.2f}")

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#121212'),  # Coal from Aleo
        hoverinfo='text',
        mode='lines',
        hovertext=edge_text
    )

    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            plot_bgcolor='#E3E3E3',  # Stone from Aleo
            paper_bgcolor='#F5F5F5',  # Ivory from Aleo
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    return fig

def research_trends_page():
    """Main function for the research trends analysis page."""
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access research trends.")
        return

    st.title("RESEARCH TRENDS ANALYSIS")

    # Research area selection
    research_area = st.text_input(
        "Enter Research Area",
        value=st.session_state.get('research_area', 'Computer Science'),
        help="Enter a specific research area to analyze trends"
    )

    if st.button("Analyze Trends", type="primary"):
        with st.spinner("Analyzing research trends..."):
            # Get trends data
            trends_data = generate_research_trends(research_area)

            if trends_data["main_topics"]:
                # Create and display network graph
                st.subheader("Research Topics Network")
                fig = create_network_graph(trends_data)
                st.plotly_chart(fig, use_container_width=True)

                # Display trends summary
                st.subheader("Key Research Topics")
                for topic in trends_data["main_topics"]:
                    importance = int(topic["weight"] * 100)
                    st.markdown(
                        f"""<div style='
                            background-color: #F5F5F5;
                            padding: 1rem;
                            border-radius: 4px;
                            border-left: 3px solid #C4F652;
                            margin-bottom: 0.5rem;
                        '>
                        <strong>{topic["name"]}</strong><br>
                        Importance: {importance}%
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.error("No trends data available. Please try again.")

if __name__ == "__main__":
    research_trends_page()