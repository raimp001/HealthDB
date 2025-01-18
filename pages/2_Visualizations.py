import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_project_data
import json

def visualization_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Data Visualizations")
    
    # Get project data
    try:
        project_data = get_project_data(1)  # Default project ID for now
        
        if not project_data:
            st.info("No data available for visualization. Please upload data first.")
            return
        
        # Convert the latest data to DataFrame
        latest_data = json.loads(project_data[0]['data_value'])
        df = pd.DataFrame(latest_data)
        
        # Visualization options
        st.subheader("Create Visualization")
        
        viz_type = st.selectbox(
            "Select Visualization Type",
            ["Line Plot", "Scatter Plot", "Bar Chart", "Box Plot", "Histogram"]
        )
        
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        
        if viz_type in ["Line Plot", "Scatter Plot"]:
            x_col = st.selectbox("Select X-axis", df.columns)
            y_col = st.selectbox("Select Y-axis", numeric_columns)
            
            if viz_type == "Line Plot":
                fig = px.line(df, x=x_col, y=y_col)
            else:
                fig = px.scatter(df, x=x_col, y=y_col)
        
        elif viz_type == "Bar Chart":
            x_col = st.selectbox("Select Category", df.columns)
            y_col = st.selectbox("Select Value", numeric_columns)
            fig = px.bar(df, x=x_col, y=y_col)
        
        elif viz_type == "Box Plot":
            y_col = st.selectbox("Select Value", numeric_columns)
            fig = px.box(df, y=y_col)
        
        else:  # Histogram
            col = st.selectbox("Select Column", numeric_columns)
            fig = px.histogram(df, x=col)
        
        # Update layout
        fig.update_layout(
            title=f"{viz_type} of {y_col if viz_type != 'Histogram' else col}",
            template="plotly_white"
        )
        
        # Display plot
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")

if __name__ == "__main__":
    visualization_page()
