import streamlit as st
from database import (
    get_database_connection,
    submit_irb_application,
    get_irb_submissions,
    submit_irb_review,
    get_institutions_for_selection,
    get_submission_approvals,
    update_institutional_approval,
    init_database
)
import pandas as pd
from datetime import datetime
from psycopg2.extras import RealDictCursor
from components.navigation import render_navigation

def get_institutions():
    """Get list of participating institutions."""
    conn = get_database_connection()
    query = "SELECT id, name FROM institutions ORDER BY name;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def irb_portal():
    # Set up demo user if not logged in
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        # Instead of requiring login, use a demo user ID
        st.session_state.user_id = 1  # Use a default user ID for demonstration
        st.session_state.username = "Demo User"

        # Create a notice that we're in demo mode
        st.info("You are viewing the IRB Portal in demonstration mode. No login required.")

    # Render consistent navigation
    render_navigation()

    st.title("IRB Submission Portal")

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .irb-section {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .status-pending {
            color: #FFC107;
            font-weight: bold;
        }
        .status-approved {
            color: #4CAF50;
            font-weight: bold;
        }
        .status-rejected {
            color: #F44336;
            font-weight: bold;
        }
        .form-section {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(0,0,0,0.05);
        }
        .submission-card {
            border-left: 4px solid #6C63FF;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #ffffff;
            border-radius: 0.3rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .review-form {
            border-left: 4px solid #4CAF50;
            padding: 1rem;
            margin-top: 1rem;
            background-color: #ffffff;
            border-radius: 0.3rem;
        }
        .approval-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            margin: 0.25rem;
            border-radius: 1rem;
            font-size: 0.8rem;
        }
        .approval-pending {
            background-color: #FFC107;
            color: #333;
        }
        .approval-approved {
            background-color: #4CAF50;
            color: white;
        }
        .approval-rejected {
            background-color: #F44336;
            color: white;
        }
        .approval-card {
            background-color: #f8f9fa;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 0.25rem;
        }
        .workflow-step {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .workflow-number {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background-color: #6C63FF;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 0.75rem;
            font-weight: bold;
        }
        .workflow-text {
            flex: 1;
        }
        .workflow-status {
            margin-left: 0.75rem;
        }
        .protocol-header {
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(0,0,0,0.1);
            padding-bottom: 0.5rem;
        }
        .protocol-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        .protocol-table th {
            text-align: left;
            background-color: #f1f1f1;
            padding: 0.5rem;
            font-weight: 500;
            border: 1px solid #ddd;
        }
        .protocol-table td {
            padding: 0.5rem;
            border: 1px solid #ddd;
        }
        .section-title {
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        .required-field::after {
            content: " *";
            color: #F44336;
        }
        .form-navigation {
            display: flex;
            justify-content: space-between;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(0,0,0,0.1);
        }
        .progress-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 1rem;
        }
        .progress-step {
            width: 0.75rem;
            height: 0.75rem;
            border-radius: 50%;
            background-color: rgba(0,0,0,0.1);
            margin: 0 0.25rem;
        }
        .progress-step.active {
            background-color: #6C63FF;
        }
        .stButton > button {
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
        }
        .help-text {
            font-size: 0.8rem;
            color: rgba(0,0,0,0.6);
            margin-top: 0.25rem;
        }
        .change-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1rem;
        }
        .change-table th, .change-table td {
            padding: 0.5rem;
            border: 1px solid #ddd;
            text-align: left;
        }
        .change-table th {
            background-color: #f1f1f1;
        }
        .toc-section {
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Tabs for different IRB portal sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "Submit IRB Application",
        "My Submissions",
        "Review Applications",
        "Institutional Approvals"
    ])

    with tab1:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("New IRB Submission")

        # Get institutions for dropdown
        try:
            # Make sure database is initialized
            if not st.session_state.get('db_initialized', False):
                init_database()
                st.session_state.db_initialized = True

            institutions = get_institutions()
            if len(institutions) == 0:
                # Create some example institutions if none exist
                conn = get_database_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO institutions (name, type, country)
                    VALUES 
                        ('University of Research', 'University', 'USA'),
                        ('Medical Research Institute', 'Research Institute', 'USA'),
                        ('City Hospital', 'Hospital', 'USA'),
                        ('Global Health Organization', 'Non-profit', 'International')
                    ON CONFLICT (name) DO NOTHING;
                """)
                conn.commit()
                cur.close()
                conn.close()

                # Reload institutions
                institutions = get_institutions()
                if len(institutions) == 0:
                    st.error("Could not create example institutions. Please contact an administrator.")
                    return
        except Exception as e:
            st.error(f"Error loading institutions: {str(e)}")
            # Create a default empty dataframe for demo purposes
            institutions = pd.DataFrame({'id': [1], 'name': ['Demo Institution']})

        # Initialize form state if not present
        if 'irb_form_step' not in st.session_state:
            st.session_state.irb_form_step = 1
            st.session_state.irb_form_data = {}

        # Function to update form state
        def update_form_state(step_direction):
            current_step = st.session_state.irb_form_step
            if step_direction == "next" and current_step < 9:
                st.session_state.irb_form_step += 1
            elif step_direction == "prev" and current_step > 1:
                st.session_state.irb_form_step -= 1
            elif step_direction == "reset":
                st.session_state.irb_form_step = 1
                st.session_state.irb_form_data = {}

        # Display progress indicator
        st.markdown('<div class="progress-indicator">', unsafe_allow_html=True)
        for i in range(1, 10):
            active_class = "active" if i <= st.session_state.irb_form_step else ""
            st.markdown(f'<div class="progress-step {active_class}"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # IRB Submission Form - Updated with protocol template structure and multi-step form
        with st.form(f"irb_submission_form_step_{st.session_state.irb_form_step}", clear_on_submit=False):

            # Step 1: Protocol Information
            if st.session_state.irb_form_step == 1:
                st.markdown('<div class="form-section protocol-header">', unsafe_allow_html=True)
                st.subheader("Step 1: Protocol Information")

                # Protocol Header Information
                st.markdown("""
                <table class="protocol-table">
                    <tr>
                        <th width="30%">Field</th>
                        <th width="70%">Value</th>
                    </tr>
                </table>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<label class="required-field">Study Title</label>', unsafe_allow_html=True)
                    title = st.text_input(
                        "Study Title", 
                        value=st.session_state.irb_form_data.get("title", ""),
                        label_visibility="collapsed",
                        help="Full title of the research project"
                    )
                    st.session_state.irb_form_data["title"] = title

                    protocol_number = st.text_input(
                        "Protocol Number", 
                        value=st.session_state.irb_form_data.get("protocol_number", ""),
                        help="The unique identifier for this protocol"
                    )
                    st.session_state.irb_form_data["protocol_number"] = protocol_number

                    version_number = st.text_input(
                        "Version Number", 
                        value=st.session_state.irb_form_data.get("version_number", "1.0"),
                        placeholder="1.0"
                    )
                    st.session_state.irb_form_data["version_number"] = version_number

                with col2:
                    version_date = st.date_input(
                        "Version Date", 
                        value=st.session_state.irb_form_data.get("version_date", datetime.now()),
                        help="Date of this protocol version"
                    )
                    st.session_state.irb_form_data["version_date"] = version_date

                    irb_number = st.text_input(
                        "IRB#", 
                        value=st.session_state.irb_form_data.get("irb_number", ""),
                        help="Will be assigned after submission if approved"
                    )
                    st.session_state.irb_form_data["irb_number"] = irb_number

                # Principal Investigator and Institution
                st.subheader("Principal Investigator Information")

                st.markdown('<label class="required-field">Primary Institution</label>', unsafe_allow_html=True)
                institution_id = st.selectbox(
                    "Primary Institution",
                    options=institutions['id'].tolist(),
                    format_func=lambda x: institutions[
                        institutions['id'] == x
                    ]['name'].iloc[0],
                    index=0,
                    label_visibility="collapsed"
                )
                st.session_state.irb_form_data["institution_id"] = institution_id

                pi_name = st.text_input(
                    "Principal Investigator Name",
                    value=st.session_state.irb_form_data.get("pi_name", ""),
                    help="Full name of the primary investigator"
                )
                st.session_state.irb_form_data["pi_name"] = pi_name

                # Multi-institutional selection
                st.subheader("Collaborating Institutions")
                st.info("Select additional institutions that need to approve this IRB submission")

                # Create a multi-select for additional institutions
                other_institutions = institutions[institutions['id'] != institution_id]
                collaborating_institutions = st.multiselect(
                    "Collaborating Institutions (Optional)",
                    options=other_institutions['id'].tolist(),
                    default=st.session_state.irb_form_data.get("collaborating_institutions", []),
                    format_func=lambda x: other_institutions[
                        other_institutions['id'] == x
                    ]['name'].iloc[0],
                    help="Select institutions that are collaborating on this research project and need to provide IRB approval"
                )
                st.session_state.irb_form_data["collaborating_institutions"] = collaborating_institutions

                # Add participating investigators
                st.subheader("Participating Investigators")

                participating_investigators = st.text_area(
                    "Participating Investigators",
                    value=st.session_state.irb_form_data.get("participating_investigators", ""),
                    help="List names and affiliations of all participating investigators, one per line"
                )
                st.session_state.irb_form_data["participating_investigators"] = participating_investigators

                st.markdown("</div>", unsafe_allow_html=True)

                # Display workflow steps
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Approval Workflow")

                workflow_steps = [
                    "Submit IRB application to your primary institution", 
                    "Application is reviewed by your primary IRB committee",
                    "Collaborating institutions review the application",
                    "When all required approvals are received, the application status changes to 'Approved'"
                ]

                for idx, step in enumerate(workflow_steps):
                    st.markdown(f"""
                    <div class="workflow-step">
                        <div class="workflow-number">{idx+1}</div>
                        <div class="workflow-text">{step}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # Step 2: Summary of Changes and TOC
            elif st.session_state.irb_form_step == 2:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 2: Summary of Changes")

                st.info("Complete this section if this is a revision to a previously submitted protocol.")

                # Summary of changes table
                st.markdown("""
                <table class="change-table">
                    <thead>
                        <tr>
                            <th width="10%">#</th>
                            <th width="20%">Section</th>
                            <th width="35%">Description of Change</th>
                            <th width="35%">Justification for Revision</th>
                        </tr>
                    </thead>
                </table>
                """, unsafe_allow_html=True)

                # Add up to 5 changes
                for i in range(1, 6):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        change_section = st.text_input(
                            f"Section {i}",
                            value=st.session_state.irb_form_data.get(f"change_section_{i}", ""),
                            key=f"section_{i}"
                        )
                        st.session_state.irb_form_data[f"change_section_{i}"] = change_section

                    with col2:
                        change_description = st.text_area(
                            f"Change Description {i}",
                            value=st.session_state.irb_form_data.get(f"change_description_{i}", ""),
                            key=f"desc_{i}",
                            height=80
                        )
                        st.session_state.irb_form_data[f"change_description_{i}"] = change_description

                    with col3:
                        change_justification = st.text_area(
                            f"Justification {i}",
                            value=st.session_state.irb_form_data.get(f"change_justification_{i}", ""),
                            key=f"justification_{i}",
                            height=80
                        )
                        st.session_state.irb_form_data[f"change_justification_{i}"] = change_justification

                st.markdown('</div>', unsafe_allow_html=True)

                # Table of Contents
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Table of Contents")

                st.info("The table of contents will be automatically generated from your completed sections.")

                # Display sample TOC
                st.markdown("""
                <div class="toc-section">1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE</div>
                <div class="toc-section">&nbsp;&nbsp;1.1 Study Rationale</div>
                <div class="toc-section">2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS</div>
                <div class="toc-section">&nbsp;&nbsp;2.1 Primary Objective and Endpoint</div>
                <div class="toc-section">&nbsp;&nbsp;2.2 Secondary Objectives</div>
                <div class="toc-section">&nbsp;&nbsp;2.3 Study Design</div>
                <div class="toc-section">&nbsp;&nbsp;2.4 Study Setting</div>
                <div class="toc-section">&nbsp;&nbsp;2.5 Date Range of the Study</div>
                <div class="toc-section">3. STUDY POPULATION</div>
                <div class="toc-section">4. STUDY PROCEDURES</div>
                <div class="toc-section">5. STATISTICAL CONSIDERATIONS</div>
                <div class="toc-section">6. STUDY ADMINISTRATION</div>
                <div class="toc-section">7. REFERENCES</div>
                """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # List of Tables and Figures
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("List of Tables and Figures")

                tables_list = st.text_area(
                    "List of Tables",
                    value=st.session_state.irb_form_data.get("tables_list", ""),
                    help="List all tables that will be included in your protocol"
                )
                st.session_state.irb_form_data["tables_list"] = tables_list

                figures_list = st.text_area(
                    "List of Figures",
                    value=st.session_state.irb_form_data.get("figures_list", ""),
                    help="List all figures that will be included in your protocol"
                )
                st.session_state.irb_form_data["figures_list"] = figures_list

                st.markdown('</div>', unsafe_allow_html=True)

            # Step 3: Background and Rationale
            elif st.session_state.irb_form_step == 3:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 3: Background Information and Scientific Rationale")

                st.markdown('<label class="required-field">Background Information</label>', unsafe_allow_html=True)
                background = st.text_area(
                    "Background Information",
                    value=st.session_state.irb_form_data.get("background", ""),
                    label_visibility="collapsed",
                    help="Provide background information on the research area, including description of the condition/issue, current state of knowledge, and relevant previous findings",
                    height=150
                )
                st.session_state.irb_form_data["background"] = background

                st.markdown('<label class="required-field">Study Rationale</label>', unsafe_allow_html=True)
                rationale = st.text_area(
                    "Study Rationale",
                    value=st.session_state.irb_form_data.get("rationale", ""),
                    label_visibility="collapsed",
                    help="Explain the rationale for conducting this specific study, including purpose and potential contributions to scientific knowledge and clinical implications",
                    height=100
                )
                st.session_state.irb_form_data["rationale"] = rationale
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 4: Study Design and Objectives
            elif st.session_state.irb_form_step == 4:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 4: Study Design, Objectives and Endpoints")

                st.markdown('<label class="required-field">Primary Objective and Endpoint</label>', unsafe_allow_html=True)
                primary_objective = st.text_area(
                    "Primary Objective and Endpoint",
                    value=st.session_state.irb_form_data.get("primary_objective", ""),
                    label_visibility="collapsed",
                    help="State the primary objective of the study and the main outcome measure(s)",
                    height=100
                )
                st.session_state.irb_form_data["primary_objective"] = primary_objective

                secondary_objectives = st.text_area(
                    "Secondary Objectives (Optional)",
                    value=st.session_state.irb_form_data.get("secondary_objectives", ""),
                    help="List additional objectives of the study, if applicable",
                    height=100
                )
                st.session_state.irb_form_data["secondary_objectives"] = secondary_objectives

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<label class="required-field">Study Type</label>', unsafe_allow_html=True)
                    study_type_options = [
                        "Retrospective cohort study", 
                        "Prospective cohort", 
                        "Randomized controlled trial",
                        "Case-control study",
                        "Cross-sectional study",
                        "Observational study",
                        "Other"
                    ]
                    study_type_index = 0
                    if "study_type" in st.session_state.irb_form_data:
                        if st.session_state.irb_form_data["study_type"] in study_type_options:
                            study_type_index = study_type_options.index(st.session_state.irb_form_data["study_type"])

                    study_type = st.selectbox(
                        "Study Type",
                        options=study_type_options,
                        index=study_type_index,
                        label_visibility="collapsed"
                    )
                    st.session_state.irb_form_data["study_type"] = study_type

                with col2:
                    st.markdown('<label class="required-field">Study Setting</label>', unsafe_allow_html=True)
                    study_setting = st.text_input(
                        "Study Setting",
                        value=st.session_state.irb_form_data.get("study_setting", ""),
                        label_visibility="collapsed",
                        help="Describe where the study will be conducted"
                    )
                    st.session_state.irb_form_data["study_setting"] = study_setting

                st.markdown('<label class="required-field">Research Methodology</label>', unsafe_allow_html=True)
                methodology = st.text_area(
                    "Research Methodology",
                    value=st.session_state.irb_form_data.get("methodology", ""),
                    label_visibility="collapsed",
                    help="Describe your research methods, including data collection procedures",
                    height=150
                )
                st.session_state.irb_form_data["methodology"] = methodology

                date_range = st.text_input(
                    "Date Range of the Study",
                    value=st.session_state.irb_form_data.get("date_range", ""),
                    help="Specify the time period covered by the study"
                )
                st.session_state.irb_form_data["date_range"] = date_range

                st.markdown('</div>', unsafe_allow_html=True)

            # Step 5: Study Population
            elif st.session_state.irb_form_step == 5:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 5: Study Population")

                st.markdown('<label class="required-field">Study Population Overview</label>', unsafe_allow_html=True)
                population_overview = st.text_area(
                    "Study Population Overview",
                    value=st.session_state.irb_form_data.get("population_overview", ""),
                    label_visibility="collapsed",
                    help="Provide an overview of the study population, including estimated sample size",
                    height=100
                )
                st.session_state.irb_form_data["population_overview"] = population_overview

                st.markdown('<label class="required-field">Inclusion Criteria</label>', unsafe_allow_html=True)
                inclusion_criteria = st.text_area(
                    "Inclusion Criteria",
                    value=st.session_state.irb_form_data.get("inclusion_criteria", ""),
                    label_visibility="collapsed",
                    help="List criteria that define who will be included in your study",
                    height=100
                )
                st.session_state.irb_form_data["inclusion_criteria"] = inclusion_criteria

                st.markdown('<label class="required-field">Exclusion Criteria</label>', unsafe_allow_html=True)
                exclusion_criteria = st.text_area(
                    "Exclusion Criteria",
                    value=st.session_state.irb_form_data.get("exclusion_criteria", ""),
                    label_visibility="collapsed",
                    help="List criteria that would exclude an individual from participating",
                    height=100
                )
                st.session_state.irb_form_data["exclusion_criteria"] = exclusion_criteria

                vulnerable_populations = st.text_area(
                    "Vulnerable Populations",
                    value=st.session_state.irb_form_data.get("vulnerable_populations", ""),
                    help="State whether vulnerable populations will be included and provide justification if applicable",
                    height=100
                )
                st.session_state.irb_form_data["vulnerable_populations"] = vulnerable_populations

                recruitment_methods = st.text_area(
                    "Recruitment Methods",
                    value=st.session_state.irb_form_data.get("recruitment_methods", ""),
                    help="Describe methods for identifying and recruiting participants, if applicable",
                    height=100
                )
                st.session_state.irb_form_data["recruitment_methods"] = recruitment_methods

                st.markdown('</div>', unsafe_allow_html=True)

            # Step 6: Study Procedures
            elif st.session_state.irb_form_step == 6:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 6: Study Procedures")

                study_procedures_overview = st.text_area(
                    "Study Procedures Overview",
                    value=st.session_state.irb_form_data.get("study_procedures_overview", ""),
                    help="Provide an overview of study procedures",
                    height=100
                )
                st.session_state.irb_form_data["study_procedures_overview"] = study_procedures_overview

                st.markdown('<label class="required-field">Data Sources</label>', unsafe_allow_html=True)
                data_sources = st.text_area(
                    "Data Sources",
                    value=st.session_state.irb_form_data.get("data_sources", ""),
                    label_visibility="collapsed",
                    help="Specify the data sources that will be used",
                    height=100
                )
                st.session_state.irb_form_data["data_sources"] = data_sources

                case_ascertainment = st.text_area(
                    "Case Ascertainment",
                    value=st.session_state.irb_form_data.get("case_ascertainment", ""),
                    help="Explain how cases will be identified and confirmed",
                    height=100
                )
                st.session_state.irb_form_data["case_ascertainment"] = case_ascertainment

                st.markdown('<label class="required-field">Variable Abstraction</label>', unsafe_allow_html=True)
                variable_abstraction = st.text_area(
                    "Variable Abstraction",
                    value=st.session_state.irb_form_data.get("variable_abstraction", ""),
                    label_visibility="collapsed",
                    help="List the variables to be collected (demographics, clinical characteristics, laboratory data, outcome measures, etc.)",
                    height=100
                )
                st.session_state.irb_form_data["variable_abstraction"] = variable_abstraction
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 7: Statistical Considerations
            elif st.session_state.irb_form_step == 7:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 7: Statistical Considerations")

                endpoints_restatement = st.text_area(
                    "Primary and Secondary Endpoints",
                    value=st.session_state.irb_form_data.get("endpoints_restatement", ""),
                    help="Reiterate the primary and secondary endpoints that will be analyzed",
                    height=100
                )
                st.session_state.irb_form_data["endpoints_restatement"] = endpoints_restatement

                primary_analysis = st.text_area(
                    "Primary Objective Analysis",
                    value=st.session_state.irb_form_data.get("primary_analysis", ""),
                    help="Describe the statistical approach for addressing the primary objective",
                    height=100
                )
                st.session_state.irb_form_data["primary_analysis"] = primary_analysis

                secondary_analysis = st.text_area(
                    "Secondary Objective Analysis",
                    value=st.session_state.irb_form_data.get("secondary_analysis", ""),
                    help="Describe the statistical approach for addressing secondary objectives",
                    height=100
                )
                st.session_state.irb_form_data["secondary_analysis"] = secondary_analysis

                bias_measures = st.text_area(
                    "Measures to Avoid Bias",
                    value=st.session_state.irb_form_data.get("bias_measures", ""),
                    help="Describe strategies to minimize bias in the study design and analysis",
                    height=100
                )
                st.session_state.irb_form_data["bias_measures"] = bias_measures

                st.markdown('<label class="required-field">Statistical Methods</label>', unsafe_allow_html=True)
                statistical_methods = st.text_area(
                    "Statistical Methods",
                    value=st.session_state.irb_form_data.get("statistical_methods", ""),
                    label_visibility="collapsed",
                    help="Provide information on descriptive analyses, primary/secondary analyses, and statistical software to be used",
                    height=100
                )
                st.session_state.irb_form_data["statistical_methods"] = statistical_methods

                sample_size = st.text_area(
                    "Sample Size Determination",
                    value=st.session_state.irb_form_data.get("sample_size", ""),
                    help="Explain how the sample size was determined, including power calculations if applicable",
                    height=100
                )
                st.session_state.irb_form_data["sample_size"] = sample_size
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 8: Study Administration and Ethics
            elif st.session_state.irb_form_step == 8:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 8: Study Administration")

                data_management = st.text_area(
                    "Data Collection and Management",
                    value=st.session_state.irb_form_data.get("data_management", ""),
                    help="Describe procedures for data collection, entry, validation, and storage",
                    height=100
                )
                st.session_state.irb_form_data["data_management"] = data_management

                confidentiality = st.text_area(
                    "Confidentiality",
                    value=st.session_state.irb_form_data.get("confidentiality", ""),
                    help="Explain measures to protect participant confidentiality",
                    height=100
                )
                st.session_state.irb_form_data["confidentiality"] = confidentiality

                results_sharing = st.text_area(
                    "Sharing of Results with Subjects",
                    value=st.session_state.irb_form_data.get("results_sharing", ""),
                    help="Specify whether and how results will be shared with study participants",
                    height=100
                )
                st.session_state.irb_form_data["results_sharing"] = results_sharing

                data_banking = st.text_area(
                    "Data and Specimen Banking",
                    value=st.session_state.irb_form_data.get("data_banking", ""),
                    help="Describe plans for data retention and future use, if applicable",
                    height=100
                )
                st.session_state.irb_form_data["data_banking"] = data_banking

                regulatory_considerations = st.text_area(
                    "Regulatory and Ethical Considerations",
                    value=st.session_state.irb_form_data.get("regulatory_considerations", ""),
                    help="Address regulatory requirements and ethical concerns",
                    height=100
                )
                st.session_state.irb_form_data["regulatory_considerations"] = regulatory_considerations

                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Risk-Benefit Assessment & Ethical Considerations")

                st.markdown('<label class="required-field">Risks and Benefits</label>', unsafe_allow_html=True)
                risks_and_benefits = st.text_area(
                    "Risks and Benefits",
                    value=st.session_state.irb_form_data.get("risks_and_benefits", ""),
                    label_visibility="collapsed",
                    help="Detail potential risks to participants and expected benefits of the research",
                    height=100
                )
                st.session_state.irb_form_data["risks_and_benefits"] = risks_and_benefits

                st.markdown('<label class="required-field">Consent Process</label>', unsafe_allow_html=True)
                consent_process = st.text_area(
                    "Consent Process",
                    value=st.session_state.irb_form_data.get("consent_process", ""),
                    label_visibility="collapsed",
                    help="Explain how you will obtain informed consent from participants",
                    height=100
                )
                st.session_state.irb_form_data["consent_process"] = consent_process

                st.markdown('<label class="required-field">Data Safety and Privacy</label>', unsafe_allow_html=True)
                data_safety_plan = st.text_area(
                    "Data Safety and Privacy",
                    value=st.session_state.irb_form_data.get("data_safety_plan", ""),
                    label_visibility="collapsed",
                    help="Describe how you will protect participant data and maintain confidentiality",
                    height=100
                )
                st.session_state.irb_form_data["data_safety_plan"] = data_safety_plan

                reportable_events = st.text_area(
                    "Reportable Events",
                    value=st.session_state.irb_form_data.get("reportable_events", ""),
                    help="Describe procedures for reporting adverse events or protocol violations",
                    height=100
                )
                st.session_state.irb_form_data["reportable_events"] = reportable_events

                # HIPAA waiver options
                hipaa_waiver = st.selectbox(
                    "HIPAA Authorization",
                    options=["Full HIPAA Authorization Required", "Partial Waiver Requested", "Full Waiver Requested", "Not Applicable"],
                    index=0
                )
                st.session_state.irb_form_data["hipaa_waiver"] = hipaa_waiver

                if hipaa_waiver in ["Partial Waiver Requested", "Full Waiver Requested"]:
                    hipaa_justification = st.text_area(
                        "HIPAA Waiver Justification",
                        value=st.session_state.irb_form_data.get("hipaa_justification", ""),
                        help="Provide justification for the HIPAA waiver request",
                        height=100
                    )
                    st.session_state.irb_form_data["hipaa_justification"] = hipaa_justification

                st.markdown('</div>', unsafe_allow_html=True)

            # Step 9: Timeline, References and Final Submission
            elif st.session_state.irb_form_step == 9:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 9: Timeline and References")

                timeline = st.text_area(
                    "Project Timeline",
                    value=st.session_state.irb_form_data.get("timeline", ""),
                    help="Present a timeline of project activities and expected completion dates",
                    height=100
                )
                st.session_state.irb_form_data["timeline"] = timeline

                protocol_review = st.text_area(
                    "Protocol Review and Amendments",
                    value=st.session_state.irb_form_data.get("protocol_review", ""),
                    help="Explain procedures for protocol review and amendment approval",
                    height=100
                )
                st.session_state.irb_form_data["protocol_review"] = protocol_review

                references = st.text_area(
                    "References",
                    value=st.session_state.irb_form_data.get("references", ""),
                    help="List all references cited in the protocol",
                    height=100
                )
                st.session_state.irb_form_data["references"] = references
                st.markdown('</div>', unsafe_allow_html=True)

                # Summary of submission
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Summary of Submission")

                # Check for missing required fields
                required_fields = {
                    "title": "Study Title", 
                    "institution_id": "Primary Institution",
                    "background": "Background Information",
                    "rationale": "Study Rationale",
                    "primary_objective": "Primary Objective",
                    "study_type": "Study Type",
                    "study_setting": "Study Setting",
                    "methodology": "Research Methodology",
                    "population_overview": "Study Population Overview",
                    "inclusion_criteria": "Inclusion Criteria",
                    "exclusion_criteria": "Exclusion Criteria",
                    "data_sources": "Data Sources",
                    "variable_abstraction": "Variable Abstraction",
                    "statistical_methods": "Statistical Methods",
                    "risks_and_benefits": "Risks and Benefits",
                    "consent_process": "Consent Process",
                    "data_safety_plan": "Data Safety and Privacy"
                }

                missing_fields = []
                for field, label in required_fields.items():
                    if field not in st.session_state.irb_form_data or not st.session_state.irb_form_data[field]:
                        missing_fields.append(label)

                if missing_fields:
                    st.error(f"Please complete the following required fields before submitting: {', '.join(missing_fields)}")
                else:
                    st.success("All required fields are completed. You can now submit your IRB application.")

                    # Display submission overview
                    with st.expander("View Complete Protocol (Click to expand)"):
                        st.write(f"**Study Title:** {st.session_state.irb_form_data['title']}")
                        st.write(f"**Protocol Number:** {st.session_state.irb_form_data['protocol_number']}")
                        st.write(f"**Version:** {st.session_state.irb_form_data['version_number']}")
                        st.write(f"**Date:** {st.session_state.irb_form_data['version_date']}")

                        st.subheader("Principal Investigator")
                        pi_name_display = st.session_state.irb_form_data.get("pi_name", "Not specified")
                        institution_name = institutions[institutions['id'] == st.session_state.irb_form_data['institution_id']]['name'].iloc[0]
                        st.write(f"{pi_name_display}, {institution_name}")

                        if st.session_state.irb_form_data.get("participating_investigators"):
                            st.subheader("Participating Investigators")
                            st.write(st.session_state.irb_form_data['participating_investigators'])

                        # Summary of Changes section if any changes were entered
                        has_changes = False
                        for i in range(1, 6):
                            if st.session_state.irb_form_data.get(f"change_section_{i}") or st.session_state.irb_form_data.get(f"change_description_{i}"):
                                has_changes = True
                                break

                        if has_changes:
                            st.subheader("SUMMARY OF CHANGES")
                            for i in range(1, 6):
                                section = st.session_state.irb_form_data.get(f"change_section_{i}")
                                desc = st.session_state.irb_form_data.get(f"change_description_{i}")
                                justification = st.session_state.irb_form_data.get(f"change_justification_{i}")
                                if section or desc:
                                    st.write(f"**{i}.** **Section:** {section} **Change:** {desc} **Justification:** {justification}")

                        st.subheader("1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE")
                        st.write(st.session_state.irb_form_data['background'])

                        st.write("**Study Rationale:**")
                        st.write(st.session_state.irb_form_data['rationale'])

                        st.subheader("2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS")
                        st.write("**Primary Objective and Endpoint:**")
                        st.write(st.session_state.irb_form_data['primary_objective'])

                        if st.session_state.irb_form_data['secondary_objectives']:
                            st.write("**Secondary Objectives:**")
                            st.write(st.session_state.irb_form_data['secondary_objectives'])

                        st.write(f"**Study Type:** {st.session_state.irb_form_data['study_type']}")
                        st.write(f"**Study Setting:** {st.session_state.irb_form_data['study_setting']}")

                        if st.session_state.irb_form_data.get("date_range"):
                            st.write(f"**Date Range:** {st.session_state.irb_form_data['date_range']}")

                        st.write("**Research Methodology:**")
                        st.write(st.session_state.irb_form_data['methodology'])

                        st.subheader("3. STUDY POPULATION")
                        st.write(st.session_state.irb_form_data['population_overview'])

                        st.write("**Inclusion Criteria:**")
                        st.write(st.session_state.irb_form_data['inclusion_criteria'])

                        st.write("**Exclusion Criteria:**")
                        st.write(st.session_state.irb_form_data['exclusion_criteria'])

                        if st.session_state.irb_form_data.get("vulnerable_populations"):
                            st.write("**Vulnerable Populations:**")
                            st.write(st.session_state.irb_form_data['vulnerable_populations'])

                        if st.session_state.irb_form_data.get("recruitment_methods"):
                            st.write("**Recruitment Methods:**")
                            st.write(st.session_state.irb_form_data['recruitment_methods'])

                        # Continue displaying other sections
                        st.subheader("4. STUDY PROCEDURES")
                        if st.session_state.irb_form_data.get("study_procedures_overview"):
                            st.write(st.session_state.irb_form_data['study_procedures_overview'])

                        st.write("**Data Sources:**")
                        st.write(st.session_state.irb_form_data['data_sources'])

                        if st.session_state.irb_form_data.get("case_ascertainment"):
                            st.write("**Case Ascertainment:**")
                            st.write(st.session_state.irb_form_data['case_ascertainment'])

                        st.write("**Variable Abstraction:**")
                        st.write(st.session_state.irb_form_data['variable_abstraction'])

                        # Section 5: Statistical Considerations
                        st.subheader("5. STATISTICAL CONSIDERATIONS")

                        if st.session_state.irb_form_data.get("endpoints_restatement"):
                            st.write("**Primary and Secondary Endpoints:**")
                            st.write(st.session_state.irb_form_data['endpoints_restatement'])

                        if st.session_state.irb_form_data.get("primary_analysis"):
                            st.write("**Primary Objective Analysis:**")
                            st.write(st.session_state.irb_form_data['primary_analysis'])

                        if st.session_state.irb_form_data.get("secondary_analysis"):
                            st.write("**Secondary Objective Analysis:**")
                            st.write(st.session_state.irb_form_data['secondary_analysis'])

                        if st.session_state.irb_form_data.get("bias_measures"):
                            st.write("**Measures to Avoid Bias:**")
                            st.write(st.session_state.irb_form_data['bias_measures'])

                        st.write("**Statistical Methods:**")
                        st.write(st.session_state.irb_form_data['statistical_methods'])

                        if st.session_state.irb_form_data.get("sample_size"):
                            st.write("**Sample Size Determination:**")
                            st.write(st.session_state.irb_form_data['sample_size'])

                        # Section 6: Study Administration
                        st.subheader("6. STUDY ADMINISTRATION")

                        if st.session_state.irb_form_data.get("data_management"):
                            st.write("**Data Collection and Management:**")
                            st.write(st.session_state.irb_form_data['data_management'])

                        if st.session_state.irb_form_data.get("confidentiality"):
                            st.write("**Confidentiality:**")
                            st.write(st.session_state.irb_form_data['confidentiality'])

                        if st.session_state.irb_form_data.get("results_sharing"):
                            st.write("**Sharing of Results with Subjects:**")
                            st.write(st.session_state.irb_form_data['results_sharing'])

                        if st.session_state.irb_form_data.get("data_banking"):
                            st.write("**Data and Specimen Banking:**")
                            st.write(st.session_state.irb_form_data['data_banking'])

                        if st.session_state.irb_form_data.get("regulatory_considerations"):
                            st.write("**Regulatory and Ethical Considerations:**")
                            st.write(st.session_state.irb_form_data['regulatory_considerations'])

                        st.write("**Risks and Benefits:**")
                        st.write(st.session_state.irb_form_data['risks_and_benefits'])

                        st.write("**Consent Process:**")
                        st.write(st.session_state.irb_form_data['consent_process'])

                        st.write("**Data Safety and Privacy:**")
                        st.write(st.session_state.irb_form_data['data_safety_plan'])

                        if st.session_state.irb_form_data.get("reportable_events"):
                            st.write("**Reportable Events:**")
                            st.write(st.session_state.irb_form_data['reportable_events'])

                        st.write(f"**HIPAA Authorization:** {st.session_state.irb_form_data.get('hipaa_waiver', 'Not specified')}")

                        if st.session_state.irb_form_data.get("hipaa_justification"):
                            st.write("**HIPAA Waiver Justification:**")
                            st.write(st.session_state.irb_form_data['hipaa_justification'])

                        # Section 7: Timeline and References
                        if st.session_state.irb_form_data.get("timeline"):
                            st.subheader("Timeline")
                            st.write(st.session_state.irb_form_data['timeline'])

                        if st.session_state.irb_form_data.get("protocol_review"):
                            st.write("**Protocol Review and Amendments:**")
                            st.write(st.session_state.irb_form_data['protocol_review'])

                        if st.session_state.irb_form_data.get("references"):
                            st.subheader("REFERENCES")
                            st.write(st.session_state.irb_form_data['references'])

                st.markdown('</div>', unsafe_allow_html=True)

            # Form navigation buttons (Previous/Next/Submit)
            st.markdown('<div class="form-navigation">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])

            # Previous button on all but first step
            with col1:
                if st.session_state.irb_form_step > 1:
                    prev_button = st.form_submit_button("← Previous Step")
                    if prev_button:
                        update_form_state("prev")
                        st.rerun()

            # Submit button on last step or Next button on other steps
            with col3:
                if st.session_state.irb_form_step == 9:
                    # Check if required fields are filled
                    can_submit = True
                    missing_fields = []
                    for field_key, field_name in required_fields.items():
                        if field_key in st.session_state.irb_form_data and not st.session_state.irb_form_data[field_key]:
                            can_submit = False
                            missing_fields.append(field_name)

                    if not can_submit:
                        with col2:
                            st.error(f"Please complete all required fields: {', '.join(missing_fields)}")

                    submitted = st.form_submit_button("Submit IRB Application")
                    if submitted:
                        if can_submit:
                            try:
                                # Include the list of collaborating institutions in the submission
                                all_institutions = [st.session_state.irb_form_data["institution_id"]] + st.session_state.irb_form_data.get("collaborating_institutions", [])

                                # Create a unified project description that includes all sections of the protocol
                                full_project_description = f"""
# {st.session_state.irb_form_data['title']}

## Protocol Information
- Protocol Number: {st.session_state.irb_form_data.get('protocol_number', 'N/A')}
- Version: {st.session_state.irb_form_data.get('version_number', '1.0')}
- Date: {st.session_state.irb_form_data.get('version_date', datetime.now()).strftime('%Y-%m-%d')}
- IRB#: {st.session_state.irb_form_data.get('irb_number', 'To be assigned')}

## 1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE
{st.session_state.irb_form_data.get('background', '')}

### Study Rationale
{st.session_state.irb_form_data.get('rationale', '')}

## 2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS
### Primary Objective and Endpoint
{st.session_state.irb_form_data.get('primary_objective', '')}

### Secondary Objectives
{st.session_state.irb_form_data.get('secondary_objectives', '')}

### Study Design
- Type: {st.session_state.irb_form_data.get('study_type', '')}
- Setting: {st.session_state.irb_form_data.get('study_setting', '')}
- Date Range: {st.session_state.irb_form_data.get('date_range', '')}

### Research Methodology
{st.session_state.irb_form_data.get('methodology', '')}

## 3. STUDY POPULATION
### Overview
{st.session_state.irb_form_data.get('population_overview', '')}

### Inclusion Criteria
{st.session_state.irb_form_data.get('inclusion_criteria', '')}

### Exclusion Criteria
{st.session_state.irb_form_data.get('exclusion_criteria', '')}

### Vulnerable Populations
{st.session_state.irb_form_data.get('vulnerable_populations', '')}

### Recruitment Methods
{st.session_state.irb_form_data.get('recruitment_methods', '')}

## 4. STUDY PROCEDURES
{st.session_state.irb_form_data.get('study_procedures_overview', '')}

### Data Sources
{st.session_state.irb_form_data.get('data_sources', '')}

### Case Ascertainment
{st.session_state.irb_form_data.get('case_ascertainment', '')}

### Variable Abstraction
{st.session_state.irb_form_data.get('variable_abstraction', '')}

## 5. STATISTICAL CONSIDERATIONS
### Primary and Secondary Endpoints
{st.session_state.irb_form_data.get('endpoints_restatement', '')}

### Primary Objective Analysis
{st.session_state.irb_form_data.get('primary_analysis', '')}

### Secondary Objective Analysis
{st.session_state.irb_form_data.get('secondary_analysis', '')}

### Measures to Avoid Bias
{st.session_state.irb_form_data.get('bias_measures', '')}

### Statistical Methods
{st.session_state.irb_form_data.get('statistical_methods', '')}

### Sample Size Determination
{st.session_state.irb_form_data.get('sample_size', '')}

## 6. STUDY ADMINISTRATION
### Data Collection and Management
{st.session_state.irb_form_data.get('data_management', '')}

### Confidentiality
{st.session_state.irb_form_data.get('confidentiality', '')}

### Sharing of Results with Subjects
{st.session_state.irb_form_data.get('results_sharing', '')}

### Data and Specimen Banking
{st.session_state.irb_form_data.get('data_banking', '')}

### Regulatory and Ethical Considerations
{st.session_state.irb_form_data.get('regulatory_considerations', '')}

### Risks and Benefits
{st.session_state.irb_form_data.get('risks_and_benefits', '')}

### Consent Process
{st.session_state.irb_form_data.get('consent_process', '')}

### Data Safety and Privacy
{st.session_state.irb_form_data.get('data_safety_plan', '')}

### Reportable Events
{st.session_state.irb_form_data.get('reportable_events', '')}

### HIPAA Authorization
{st.session_state.irb_form_data.get('hipaa_waiver', 'Full HIPAA Authorization Required')}
{st.session_state.irb_form_data.get('hipaa_justification', '')}

## 7. TIMELINE AND REFERENCES
### Timeline
{st.session_state.irb_form_data.get('timeline', '')}

### Protocol Review and Amendments
{st.session_state.irb_form_data.get('protocol_review', '')}

## REFERENCES
{st.session_state.irb_form_data.get('references', '')}
"""

                                # Submit the IRB application using the database function
                                submission_id = submit_irb_application(
                                    title=st.session_state.irb_form_data['title'],
                                    pi_id=st.session_state.user_id,
                                    institution_id=st.session_state.irb_form_data['institution_id'],
                                    project_description=full_project_description,
                                    methodology=st.session_state.irb_form_data.get('methodology', ''),
                                    risks_and_benefits=st.session_state.irb_form_data.get('risks_and_benefits', ''),
                                    participant_selection=st.session_state.irb_form_data.get('population_overview', ''),
                                    consent_process=st.session_state.irb_form_data.get('consent_process', ''),
                                    data_safety=st.session_state.irb_form_data.get('data_safety_plan', ''),
                                    collaborating_institutions=st.session_state.irb_form_data.get('collaborating_institutions', [])
                                )

                                # Reset the form state after successful submission
                                update_form_state("reset")
                                st.success("Your IRB application has been submitted successfully! The IRB committee will review your application and contact you if additional information is needed.")
                                st.info(f"Your tracking number is: IRB-{submission_id}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"An error occurred while submitting your application: {str(e)}")
                        else:
                            st.error("Please complete all required fields before submitting.")
                else:
                    next_button = st.form_submit_button("Next Step →")
                    if next_button:
                        update_form_state("next")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("My Submissions")

        try:
            # Get my submissions
            submissions = get_irb_submissions(st.session_state.user_id)

            if len(submissions) == 0:
                st.info("You haven't submitted any IRB applications yet.")
            else:
                for submission in submissions:
                    st.markdown(f"""
                    <div class="submission-card">
                        <h3>{submission['title']}</h3>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <div>Submitted on: {submission['submitted_at'].strftime('%Y-%m-%d')}</div>
                            <div class="status-{submission['status'].lower()}">{submission['status']}</div>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            {submission['institution_name']}
                        </div>
                    """, unsafe_allow_html=True)

                    # Get approval status for each institution
                    approvals = get_submission_approvals(submission['id'])
                    if len(approvals) > 0:
                        st.markdown('<div style="margin-top: 0.5rem;">', unsafe_allow_html=True)
                        st.markdown('<h4>Institutional Approvals</h4>', unsafe_allow_html=True)

                        for approval in approvals:
                            status_class = "approval-pending"
                            if approval['status'] == 'Approved':
                                status_class = "approval-approved"
                            elif approval['status'] == 'Rejected':
                                status_class = "approval-rejected"

                            st.markdown(f"""
                            <div class="approval-card">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>{approval['institution_name']}</div>
                                    <div class="{status_class} approval-badge">{approval['status']}</div>
                                </div>
                                {f"<div style='font-size: 0.9rem;'>{approval['comments']}</div>" if approval['comments'] else ""}
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

                    # Display view button
                    if st.button(f"View Details #{submission['id']}", key=f"view_{submission['id']}"):
                        # Display full application
                        st.json(submission)

                    st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading your submissions: {str(e)}")
            # Create some demo submissions
            st.markdown("""
            <div class="submission-card">
                <h3>Demo Study: CAR-T Cell Therapy for Relapsed/Refractory B-cell ALL</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <div>Submitted on: 2023-05-20</div>
                    <div class="status-pending">Pending</div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    University of Research
                </div>
                <div style="margin-top: 0.5rem;">
                    <h4>Institutional Approvals</h4>
                    <div class="approval-card">
                        <div style="display: flex; justify-content: space-between;">
                            <div>University of Research</div>
                            <div class="approval-approved approval-badge">Approved</div>
                        </div>
                    </div>
                    <div class="approval-card">
                        <div style="display: flex; justify-content: space-between;">
                            <div>Medical Research Institute</div>
                            <div class="approval-pending approval-badge">Pending</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("Review Applications")

        try:
            # In a real app, this would be filtered by the user's institution and reviewer status
            submissions = get_irb_submissions(reviewer_id=st.session_state.user_id)

            if len(submissions) == 0:
                st.info("There are no IRB applications pending your review.")
            else:
                for submission in submissions:
                    st.markdown(f"""
                    <div class="submission-card">
                        <h3>{submission['title']}</h3>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <div>Submitted on: {submission['submitted_at'].strftime('%Y-%m-%d')}</div>
                            <div>PI: {submission['pi_name']}</div>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            {submission['institution_name']}
                        </div>
                    """, unsafe_allow_html=True)

                    # Add a review section
                    with st.expander("Review Application"):
                        st.write("### Project Description")
                        st.write(submission['project_description'])

                        st.write("### Methodology")
                        st.write(submission['methodology'])

                        st.write("### Risks and Benefits")
                        st.write(submission['risks_and_benefits'])

                        st.write("### Participant Selection")
                        st.write(submission['participant_selection'])

                        st.write("### Consent Process")
                        st.write(submission['consent_process'])

                        st.write("### Data Safety")
                        st.write(submission['data_safety'])

                        # Review form
                        st.markdown('<div class="review-form">', unsafe_allow_html=True)
                        with st.form(f"review_form_{submission['id']}"):
                            st.write("### Submit Your Review")

                            decision = st.selectbox(
                                "Decision",
                                options=["Approved", "Revisions Required", "Rejected"],
                                key=f"decision_{submission['id']}"
                            )

                            comments = st.text_area(
                                "Comments",
                                key=f"comments_{submission['id']}",
                                help="Provide feedback, explain your decision, or request revisions"
                            )

                            submitted = st.form_submit_button("Submit Review")

                            if submitted:
                                # Submit the review
                                success = submit_irb_review(
                                    submission_id=submission['id'],
                                    reviewer_id=st.session_state.user_id,
                                    decision=decision,
                                    comments=comments
                                )

                                if success:
                                    st.success("Your review has been submitted successfully!")
                                else:
                                    st.error("An error occurred while submitting your review.")

                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading applications for review: {str(e)}")
            # Create a demo application for review
            st.markdown("""
            <div class="submission-card">
                <h3>Demo Study: Assessment of Novel Biomarkers in Autoimmune Disorders</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <div>Submitted on: 2023-06-12</div>
                    <div>PI: Dr. Jane Smith</div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    Medical Research Institute
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Review Application"):
                st.write("### Project Description")
                st.write("This study aims to identify novel biomarkers associated with autoimmune disorders, with a focus on rheumatoid arthritis and systemic lupus erythematosus. The project will utilize existing biobank samples and clinical data to evaluate potential correlations between biomarker profiles and disease progression.")

                st.write("### Methodology")
                st.write("A retrospective analysis of biobank samples from 200 patients with confirmed autoimmune disorders and 100 healthy controls. Samples will be analyzed using multiplex assays and advanced proteomics techniques.")

                st.write("### Risks and Benefits")
                st.write("This study poses minimal risk to participants as it utilizes existing samples. The potential benefits include identification of new diagnostic tools and therapeutic targets for autoimmune disorders.")

                # Review form
                st.markdown('<div class="review-form">', unsafe_allow_html=True)
                with st.form("demo_review_form"):
                    st.write("### Submit Your Review")

                    decision = st.selectbox(
                        "Decision",
                        options=["Approved", "Revisions Required", "Rejected"]
                    )

                    comments = st.text_area(
                        "Comments",
                        help="Provide feedback, explain your decision, or request revisions"
                    )

                    submitted = st.form_submit_button("Submit Review")

                    if submitted:
                        st.success("Your review has been submitted successfully! (Demo submission)")

                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("Institutional Approvals")

        try:
            # Get institutions that this user has permissions to approve for
            institutions = get_institutions_for_selection(st.session_state.user_id)

            if len(institutions) == 0:
                st.info("You don't have permissions to approve submissions for any institutions.")
            else:
                # Select institution to see submissions requiring approval
                institution_id = st.selectbox(
                    "Select Institution",
                    options=institutions['id'].tolist(),
                    format_func=lambda x: institutions[institutions['id'] == x]['name'].iloc[0]
                )

                # Get submissions requiring approval for this institution
                submissions = get_irb_submissions(institution_id=institution_id)

                if len(submissions) == 0:
                    st.info(f"No submissions currently require approval from {institutions[institutions['id'] == institution_id]['name'].iloc[0]}.")
                else:
                    for submission in submissions:
                        st.markdown(f"""
                        <div class="submission-card">
                            <h3>{submission['title']}</h3>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <div>Submitted on: {submission['submitted_at'].strftime('%Y-%m-%d')}</div>
                                <div>PI: {submission['pi_name']}</div>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                Primary: {submission['institution_name']}
                            </div>
                        """, unsafe_allow_html=True)

                        # Add approval form
                        with st.expander("Review for Institutional Approval"):
                            st.write("### Project Description")
                            st.write(submission['project_description'])

                            # Approval form
                            st.markdown('<div class="review-form">', unsafe_allow_html=True)
                            with st.form(f"approval_form_{submission['id']}"):
                                st.write("### Submit Institutional Approval")

                                approval_status = st.selectbox(
                                    "Status",
                                    options=["Approved", "Pending Additional Information", "Rejected"],
                                    key=f"approval_{submission['id']}"
                                )

                                approval_comments = st.text_area(
                                    "Comments",
                                    key=f"approval_comments_{submission['id']}",
                                    help="Provide feedback or requirements from your institution"
                                )

                                submitted = st.form_submit_button("Submit Institutional Decision")

                                if submitted:
                                    # Update the approval status
                                    success = update_institutional_approval(
                                        submission_id=submission['id'],
                                        institution_id=institution_id,
                                        status=approval_status,
                                        comments=approval_comments,
                                        updated_by=st.session_state.user_id
                                    )

                                    if success:
                                        st.success("Your institutional decision has been recorded successfully!")
                                    else:
                                        st.error("An error occurred while recording your decision.")

                            st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading institutional approval data: {str(e)}")
            # Create demo content
            st.info("Select an institution to view submissions requiring approval.")
            st.selectbox(
                "Select Institution (Demo)",
                options=["Medical Research Institute", "University of Research"]
            )

            st.markdown("""
            <div class="submission-card">
                <h3>Demo Study: Early Detection of Pancreatic Cancer Using ML Algorithms</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <div>Submitted on: 2023-04-30</div>
                    <div>PI: Dr. Robert Johnson</div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    Primary: University of Research
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

def main():
    irb_portal()

if __name__ == "__main__":
    main()