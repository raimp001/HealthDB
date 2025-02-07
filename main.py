import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="Research Data Management",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-container {
        max-width: 1200px;
        margin: auto;
        padding: 2rem;
    }
    .dashboard-section {
        background-color: #1E1E2F;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .data-stats {
        background-color: #252525;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .upload-area {
        border: 2px dashed #6C63FF;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: transparent;
        border: 1px solid #6C63FF;
        color: white;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #6C63FF;
        color: white;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

try:
    st.title("Research Data Management")

    # Main dashboard layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # EMR Data Extraction Section
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("EMR Data Extraction")

        # EMR connection form
        emr_type = st.selectbox(
            "EMR System",
            ["Epic Clarity", "Cerner", "AllScripts", "MEDITECH", "Other"]
        )

        connection_tabs = st.tabs(["Direct Connection", "File Import"])

        with connection_tabs[0]:
            st.subheader("Database Connection")
            emr_server = st.text_input("Database Server URL")
            credentials_method = st.radio(
                "Authentication Method",
                ["Certificate", "Username/Password", "Service Account"]
            )
            if credentials_method == "Certificate":
                st.file_uploader("Upload Certificate", type=['pem', 'crt'])
            elif credentials_method == "Username/Password":
                st.text_input("Username")
                st.text_input("Password", type="password")
            else:
                st.file_uploader("Service Account Credentials", type=['json', 'key'])

        with connection_tabs[1]:
            st.subheader("File-based Import")
            st.file_uploader("Upload EMR Export File", type=['csv', 'xlsx', 'sql'])

        # Date range selection
        date_cols = st.columns(2)
        with date_cols[0]:
            start_date = st.date_input("Start Date")
        with date_cols[1]:
            end_date = st.date_input("End Date")

        # Data selection
        st.subheader("Data Selection")
        data_categories = {
            "Clinical": ["Patient Demographics", "Diagnoses", "Procedures", "Medications", "Allergies"],
            "Laboratory": ["Lab Results", "Microbiology", "Pathology"],
            "Imaging": ["Radiology Reports", "Image Metadata"],
            "Notes": ["Progress Notes", "Discharge Summaries", "Consultation Notes"]
        }

        selected_categories = st.multiselect(
            "Select Data Categories",
            options=list(data_categories.keys())
        )

        if selected_categories:
            all_data_types = []
            for category in selected_categories:
                all_data_types.extend(data_categories[category])

            selected_data_types = st.multiselect(
                "Select Specific Data Types",
                options=all_data_types
            )

        if st.button("Extract Data"):
            with st.spinner("Preparing data extraction..."):
                st.info("Data extraction will start soon. This may take several minutes depending on the selected date range and data types.")
                # Add EMR data extraction logic here
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Data Stats Section
        st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
        st.header("Data Statistics")

        # Placeholder stats - replace with actual database queries
        st.markdown('<div class="data-stats">', unsafe_allow_html=True)
        st.metric("Total Records", "0")
        st.metric("Last Import", "Never")
        st.metric("Active Projects", "0")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Data Import Section
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    st.header("Data Import")

    import_tabs = st.tabs(["Spreadsheet Upload", "Database Import", "API Integration"])

    with import_tabs[0]:
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drop your spreadsheet here or click to upload",
            type=['csv', 'xlsx', 'xls'],
            help="Supported formats: CSV, Excel"
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.success(f"Successfully loaded {len(df)} rows of data")
                st.dataframe(df.head())

                if st.button("Import Data"):
                    # Add data import logic here
                    st.success("Data imported successfully!")

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with import_tabs[1]:
        st.write("Database connection configuration will be here")

    with import_tabs[2]:
        st.write("API integration options will be here")

    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")