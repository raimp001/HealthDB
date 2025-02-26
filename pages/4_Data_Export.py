import streamlit as st
import pandas as pd
from database import get_database_connection, get_project_data
from utils import prepare_data_export
import json
import io

def data_export_page():
    # Set up demo user if not logged in
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        # Instead of requiring login, use a demo user ID
        st.session_state.user_id = 1  # Use a default user ID for demonstration
        st.session_state.username = "Demo User"

        # Create a notice that we're in demo mode
        st.info("You are viewing the Data Export page in demonstration mode. No login required.")

    st.title("Data Export")

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .export-section {
            background-color: #1E1E2F;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .data-preview {
            background-color: #252525;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .export-options {
            background-color: #252525;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Get user's projects
        conn = get_database_connection()
        query = """
            SELECT p.id, p.name, p.description
            FROM projects p
            WHERE p.owner_id = %s
            ORDER BY p.created_at DESC;
        """

        projects_df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
        conn.close()

        if len(projects_df) == 0:
            st.info("You don't have any projects yet. Create a project first to export data.")
            return

        st.markdown('<div class="export-section">', unsafe_allow_html=True)
        st.subheader("Select Project")

        selected_project_idx = st.selectbox(
            "Choose a project",
            range(len(projects_df)),
            format_func=lambda x: f"{projects_df.iloc[x]['name']}"
        )

        selected_project_id = projects_df.iloc[selected_project_idx]['id']

        # Get available datasets for the selected project
        project_data = get_project_data(selected_project_id)

        if not project_data:
            st.info("No data available for export in this project. Please upload data first.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Dataset selection
        st.subheader("Select Dataset")

        datasets = []
        for data in project_data:
            try:
                metadata = data['metadata'] 
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                datasets.append({
                    'id': data['id'],
                    'type': data['data_type'],
                    'uploaded_at': data['uploaded_at'],
                    'rows': metadata.get('rows', 'N/A'),
                    'columns': metadata.get('columns', 'N/A')
                })
            except (json.JSONDecodeError, KeyError):
                # Handle malformed metadata
                datasets.append({
                    'id': data['id'],
                    'type': data['data_type'],
                    'uploaded_at': data['uploaded_at'],
                    'rows': 'N/A',
                    'columns': 'N/A'
                })

        selected_dataset_idx = st.selectbox(
            "Choose dataset to export",
            range(len(datasets)),
            format_func=lambda x: f"{datasets[x]['type']} - Uploaded: {datasets[x]['uploaded_at'].strftime('%Y-%m-%d %H:%M') if hasattr(datasets[x]['uploaded_at'], 'strftime') else datasets[x]['uploaded_at']}"
        )

        selected_dataset = datasets[selected_dataset_idx]

        # Preview data
        st.markdown('<div class="data-preview">', unsafe_allow_html=True)
        st.subheader("Data Preview")

        try:
            data_value = project_data[selected_dataset_idx]['data_value']
            if isinstance(data_value, str):
                data_value = json.loads(data_value)

            preview_df = pd.DataFrame(data_value)
            st.dataframe(preview_df.head(5))
            st.caption(f"Showing 5 of {len(preview_df)} rows")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            st.error(f"Error previewing data: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Export options
        st.markdown('<div class="export-options">', unsafe_allow_html=True)
        st.subheader("Export Options")

        export_format = st.selectbox(
            "Select export format",
            ["CSV", "JSON", "Excel"],
            help="Choose the file format for your exported data"
        )

        include_metadata = st.checkbox(
            "Include metadata", 
            value=True,
            help="Include dataset metadata in a separate sheet (Excel only) or as comments (CSV/JSON)"
        )

        if st.button("Export Data", use_container_width=True):
            try:
                # Get the full dataset
                data_value = project_data[selected_dataset_idx]['data_value']
                if isinstance(data_value, str):
                    data_value = json.loads(data_value)

                df = pd.DataFrame(data_value)

                # Prepare export based on format
                if export_format == "CSV":
                    output = prepare_data_export(df, 'csv', include_metadata)
                    file_extension = "csv"
                    mime = "text/csv"
                elif export_format == "JSON":
                    output = prepare_data_export(df, 'json', include_metadata)
                    file_extension = "json"
                    mime = "application/json"
                else:  # Excel
                    output = prepare_data_export(df, 'excel', include_metadata)
                    file_extension = "xlsx"
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Create download button
                st.download_button(
                    label=f"Download {export_format}",
                    data=output,
                    file_name=f"{projects_df.iloc[selected_project_idx]['name']}_{selected_dataset['type']}.{file_extension}",
                    mime=mime,
                    use_container_width=True
                )

                st.success("Data ready for download!")

            except Exception as e:
                st.error(f"Error preparing data export: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error preparing data export: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    data_export_page()