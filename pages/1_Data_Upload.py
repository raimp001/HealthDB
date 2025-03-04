import streamlit as st
import pandas as pd
from database import save_research_data
from utils import validate_data, generate_metadata
from aleo_interface import AleoInterface
from components.validation_tracker import validation_progress_tracker
from components.navigation import render_navigation
import asyncio
import json
import time

# Blockchain Storage Function
async def store_on_blockchain(data, metadata):
    """Simulate storing data on the blockchain with progress tracking."""
    aleo = AleoInterface()
    steps = []

    steps.append({"name": "Generating Data Hash", "status": "running"})
    validation_progress_tracker(steps)
    data_hash = aleo.generate_data_hash({"data": data, "metadata": metadata})
    steps[0]["status"] = "complete"
    steps[0]["details"] = f"Hash: {data_hash[:16]}..."

    steps.append({"name": "Creating Zero-Knowledge Proof", "status": "running"})
    validation_progress_tracker(steps)
    time.sleep(1)
    steps[1]["status"] = "complete"

    steps.append({"name": "Validating Proof", "status": "running"})
    validation_progress_tracker(steps)
    time.sleep(0.5)
    steps[2]["status"] = "complete"

    steps.append({"name": "Storing on Blockchain", "status": "running"})
    validation_progress_tracker(steps)
    result = await aleo.store_data_on_chain(data_hash, access_level=1)
    steps[3]["status"] = "complete"
    steps[3]["details"] = f"Transaction ID: {result['transaction_id']}"

    steps.append({"name": "Confirming Transaction", "status": "running"})
    validation_progress_tracker(steps)
    time.sleep(1)
    steps[4]["status"] = "complete"
    steps[4]["details"] = f"Block Height: {result['block_height']}"

    validation_progress_tracker(steps)
    return result

# Main Function
def data_upload_page():
    """Main function to set up the Data Upload page."""
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.session_state.user_id = 1
        st.session_state.username = "Demo User"
        st.info("You are viewing the Data Upload page in demonstration mode. No login required.")

    render_navigation()
    st.title("Data Upload")

    project_id = st.session_state.get('selected_project_id', 1)
    project_name = st.session_state.get('selected_project_name', 'Demo Project')

    if project_id != 1:
        st.subheader(f"Project: {project_name}")
    else:
        project_name = st.text_input("Project Name", "Demo Project")
        project_description = st.text_area("Project Description", "Description of research project for demonstration")

    st.subheader("Data Source")
    source_type = st.selectbox("Select data source", ["File Upload", "Database", "API"])

    if source_type == "File Upload":
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])
        if uploaded_file:
            try:
                if uploaded_file.type == "text/csv":
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.type == "application/json":
                    df = pd.read_json(uploaded_file)
                else:
                    st.error("Unsupported file type")
                    return
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())

                validation_results = validate_data(df)

                st.subheader("Data Validation Results")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Missing Values:")
                    st.write(validation_results['missing_values'])
                with col2:
                    st.write("Duplicate Rows:", validation_results['duplicate_rows'])
                    st.write("Column Types:")
                    st.write(validation_results['column_types'])

                if st.button("Save Data", key="save_data_unique_key"):
                    try:
                        metadata = generate_metadata(df)
                        blockchain_result = asyncio.run(store_on_blockchain(
                            df.to_json(orient='records'),
                            metadata
                        ))
                        metadata_dict = json.loads(metadata)
                        metadata_dict["blockchain"] = blockchain_result
                        updated_metadata = json.dumps(metadata_dict)
                        data_id = save_research_data(
                            project_id=project_id,
                            data_type=uploaded_file.type,
                            data_value=df.to_json(orient='records'),
                            metadata=updated_metadata,
                            user_id=st.session_state.user_id
                        )
                        st.success("Data saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving data: {str(e)}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

    elif source_type == "Database":
        st.write("Database extraction feature coming soon...")
        # Future implementation: Add fields for database connection and query

    elif source_type == "API":
        st.write("API extraction feature coming soon...")
        # Future implementation: Add fields for API endpoint and parameters

if __name__ == "__main__":
    data_upload_page()