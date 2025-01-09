import streamlit as st
import pandas as pd
from database import get_project_data
from utils import prepare_data_export
import json
import io

def data_export_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return
    
    st.title("Data Export")
    
    try:
        # Get available datasets
        project_data = get_project_data(1)  # Default project ID for now
        
        if not project_data:
            st.info("No data available for export. Please upload data first.")
            return
        
        # Dataset selection
        st.subheader("Select Dataset")
        
        datasets = []
        for data in project_data:
            metadata = json.loads(data['metadata'])
            datasets.append({
                'id': data['id'],
                'uploaded_at': data['uploaded_at'],
                'rows': metadata['num_rows'],
                'columns': metadata['num_columns']
            })
        
        selected_dataset = st.selectbox(
            "Choose dataset to export",
            range(len(datasets)),
            format_func=lambda x: f"Dataset {datasets[x]['id']} - Uploaded: {datasets[x]['uploaded_at']}"
        )
        
        # Export format selection
        export_format = st.selectbox(
            "Select export format",
            ["CSV", "JSON", "Excel"]
        )
        
        if st.button("Export Data"):
            # Get the selected dataset
            data = json.loads(project_data[selected_dataset]['data_value'])
            df = pd.DataFrame(data)
            
            # Prepare export
            if export_format == "CSV":
                output = prepare_data_export(df, 'csv')
                file_extension = "csv"
                mime = "text/csv"
            elif export_format == "JSON":
                output = prepare_data_export(df, 'json')
                file_extension = "json"
                mime = "application/json"
            else:  # Excel
                output = io.BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                file_extension = "xlsx"
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
            # Create download button
            st.download_button(
                label=f"Download {export_format}",
                data=output,
                file_name=f"research_data_{datasets[selected_dataset]['id']}.{file_extension}",
                mime=mime
            )
            
            st.success("Data ready for download!")
            
    except Exception as e:
        st.error(f"Error preparing data export: {str(e)}")

if __name__ == "__main__":
    data_export_page()
