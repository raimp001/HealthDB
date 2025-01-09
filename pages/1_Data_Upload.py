import streamlit as st
import pandas as pd
from database import save_research_data
from utils import validate_data, generate_metadata
from aleo_interface import AleoInterface
import asyncio
import json

async def store_on_blockchain(data, metadata):
    aleo = AleoInterface()
    data_hash = aleo.generate_data_hash({"data": data, "metadata": metadata})
    result = await aleo.store_data_on_chain(data_hash, access_level=1)
    return result

def data_upload_page():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access this page.")
        return

    st.title("Data Upload")

    # Project information
    project_name = st.text_input("Project Name")
    project_description = st.text_area("Project Description")

    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded data:")
            st.dataframe(df.head())

            # Data validation
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

            if st.button("Save Data"):
                try:
                    # Generate metadata
                    metadata = generate_metadata(df)

                    # Save to blockchain
                    with st.spinner("Storing data hash on blockchain..."):
                        blockchain_result = asyncio.run(store_on_blockchain(
                            df.to_json(orient='records'),
                            metadata
                        ))

                    # Update metadata with blockchain information
                    metadata_dict = json.loads(metadata)
                    metadata_dict["blockchain"] = blockchain_result
                    updated_metadata = json.dumps(metadata_dict)

                    # Save to database
                    data_id = save_research_data(
                        project_id=1,  # Default project ID for now
                        data_type="csv",
                        data_value=df.to_json(orient='records'),
                        metadata=updated_metadata,
                        user_id=st.session_state.user_id
                    )

                    st.success(f"""
                    Data saved successfully!
                    - Data ID: {data_id}
                    - Transaction ID: {blockchain_result['transaction_id']}
                    - Block Height: {blockchain_result['block_height']}
                    """)

                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    data_upload_page()