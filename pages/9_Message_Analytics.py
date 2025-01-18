import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import get_database_connection
import pandas as pd
from datetime import datetime, timedelta
import json

def get_message_statistics(user_id):
    """Get message statistics for the dashboard."""
    conn = get_database_connection()
    try:
        # Messages sent/received over time
        query_over_time = """
            WITH msg_stats AS (
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    COUNT(CASE WHEN sender_id = %s THEN 1 END) as sent,
                    COUNT(CASE WHEN recipient_id = %s THEN 1 END) as received
                FROM researcher_messages
                WHERE sender_id = %s OR recipient_id = %s
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY date
            )
            SELECT 
                date,
                sent,
                received,
                sent + received as total
            FROM msg_stats;
        """
        
        # Active conversations
        query_active_convs = """
            WITH recent_convos AS (
                SELECT 
                    CASE 
                        WHEN sender_id = %s THEN recipient_id
                        ELSE sender_id
                    END as conversation_partner,
                    MAX(created_at) as last_message,
                    COUNT(*) as message_count
                FROM researcher_messages
                WHERE sender_id = %s OR recipient_id = %s
                GROUP BY conversation_partner
            )
            SELECT 
                u.username as partner_name,
                rc.last_message,
                rc.message_count
            FROM recent_convos rc
            JOIN users u ON u.id = rc.conversation_partner
            ORDER BY rc.last_message DESC;
        """
        
        # Response times
        query_response_times = """
            WITH message_pairs AS (
                SELECT 
                    m1.id,
                    m1.sender_id,
                    m1.recipient_id,
                    m1.created_at as msg_time,
                    MIN(m2.created_at) as response_time
                FROM researcher_messages m1
                LEFT JOIN researcher_messages m2 ON 
                    m1.sender_id = m2.recipient_id AND
                    m1.recipient_id = m2.sender_id AND
                    m2.created_at > m1.created_at
                WHERE m1.sender_id = %s OR m1.recipient_id = %s
                GROUP BY m1.id, m1.sender_id, m1.recipient_id, m1.created_at
            )
            SELECT 
                EXTRACT(EPOCH FROM (response_time - msg_time))/3600 as response_hours
            FROM message_pairs
            WHERE response_time IS NOT NULL;
        """
        
        # Execute queries
        df_time = pd.read_sql(query_over_time, conn, params=(user_id, user_id, user_id, user_id))
        df_convos = pd.read_sql(query_active_convs, conn, params=(user_id, user_id, user_id))
        df_response = pd.read_sql(query_response_times, conn, params=(user_id, user_id))
        
        return {
            'messages_over_time': df_time,
            'active_conversations': df_convos,
            'response_times': df_response
        }
    finally:
        conn.close()

def create_message_trend_chart(df):
    """Create an interactive line chart for message trends."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['sent'],
        name='Sent',
        line=dict(color='#2196F3'),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['received'],
        name='Received',
        line=dict(color='#4CAF50'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title='Message Activity Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Messages',
        hovermode='x unified'
    )
    
    return fig

def create_response_time_histogram(df):
    """Create a histogram of response times."""
    fig = go.Figure(data=[go.Histogram(
        x=df['response_hours'],
        nbinsx=20,
        name='Response Times',
        marker_color='#673AB7'
    )])
    
    fig.update_layout(
        title='Distribution of Response Times',
        xaxis_title='Response Time (Hours)',
        yaxis_title='Frequency',
        showlegend=False
    )
    
    return fig

def message_analytics_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to view message analytics.")
        return
        
    st.title("Message Analytics Dashboard")
    
    # Get analytics data
    stats = get_message_statistics(st.session_state.user_id)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_sent = stats['messages_over_time']['sent'].sum()
        st.metric("Total Messages Sent", total_sent)
        
    with col2:
        total_received = stats['messages_over_time']['received'].sum()
        st.metric("Total Messages Received", total_received)
        
    with col3:
        active_conversations = len(stats['active_conversations'])
        st.metric("Active Conversations", active_conversations)
    
    # Message trends
    st.subheader("Message Activity Trends")
    message_trend_chart = create_message_trend_chart(stats['messages_over_time'])
    st.plotly_chart(message_trend_chart, use_container_width=True)
    
    # Response time analysis
    st.subheader("Response Time Analysis")
    if not stats['response_times'].empty:
        response_time_chart = create_response_time_histogram(stats['response_times'])
        st.plotly_chart(response_time_chart, use_container_width=True)
        
        avg_response_time = stats['response_times']['response_hours'].mean()
        st.metric(
            "Average Response Time",
            f"{avg_response_time:.1f} hours"
        )
    else:
        st.info("No response time data available yet.")
    
    # Active conversations
    st.subheader("Active Conversations")
    if not stats['active_conversations'].empty:
        st.dataframe(
            stats['active_conversations'].style.format({
                'last_message': lambda x: x.strftime('%Y-%m-%d %H:%M:%S'),
                'message_count': '{:,}'.format
            }),
            hide_index=True
        )
    else:
        st.info("No active conversations yet.")

if __name__ == "__main__":
    message_analytics_page()
