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
            if step_direction == "next" and current_step < 7:
                st.session_state.irb_form_step += 1
            elif step_direction == "prev" and current_step > 1:
                st.session_state.irb_form_step -= 1
            elif step_direction == "reset":
                st.session_state.irb_form_step = 1
                st.session_state.irb_form_data = {}

        # Display progress indicator
        st.markdown('<div class="progress-indicator">', unsafe_allow_html=True)
        for i in range(1, 8):
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

            # Step 2: Background and Rationale
            elif st.session_state.irb_form_step == 2:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 2: Background Information and Scientific Rationale")

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
                    help="Explain the scientific rationale for conducting this specific study, including purpose and potential contributions",
                    height=100
                )
                st.session_state.irb_form_data["rationale"] = rationale
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 3: Study Design and Objectives
            elif st.session_state.irb_form_step == 3:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 3: Study Design, Objectives and Endpoints")

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
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 4: Study Population
            elif st.session_state.irb_form_step == 4:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 4: Study Population")

                st.markdown('<label class="required-field">Participant Selection</label>', unsafe_allow_html=True)
                participant_selection = st.text_area(
                    "Participant Selection",
                    value=st.session_state.irb_form_data.get("participant_selection", ""),
                    label_visibility="collapsed",
                    help="Describe your participant selection criteria and recruitment process",
                    height=100
                )
                st.session_state.irb_form_data["participant_selection"] = participant_selection

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
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 5: Study Procedures
            elif st.session_state.irb_form_step == 5:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 5: Study Procedures")

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

            # Step 6: Statistical Considerations and Risk Assessment
            elif st.session_state.irb_form_step == 6:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 6: Statistical Considerations")

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
                st.markdown('</div>', unsafe_allow_html=True)

            # Step 7: Timeline, References and Final Submission
            elif st.session_state.irb_form_step == 7:
                st.markdown('<div class="form-section">', unsafe_allow_html=True)
                st.subheader("Step 7: Timeline and References")

                timeline = st.text_area(
                    "Project Timeline",
                    value=st.session_state.irb_form_data.get("timeline", ""),
                    help="Present a timeline of project activities and expected completion dates",
                    height=100
                )
                st.session_state.irb_form_data["timeline"] = timeline

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
                    "participant_selection": "Participant Selection",
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

                        st.write("**Research Methodology:**")
                        st.write(st.session_state.irb_form_data['methodology'])

                        # Continue with other sections...

                st.markdown('</div>', unsafe_allow_html=True)

            # Navigation buttons
            st.markdown('<div class="form-navigation">', unsafe_allow_html=True)

            # Previous button (not on first step)
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                if st.session_state.irb_form_step > 1:
                    prev_button = st.form_submit_button("← Previous Step")
                    if prev_button:
                        update_form_state("prev")
                        st.experimental_rerun()

            # Submit button on last step or Next button on other steps
            with col3:
                if st.session_state.irb_form_step == 7:
                    submit_button = st.form_submit_button("Submit Application")
                    if submit_button:
                        # Check for missing required fields
                        missing_fields = []
                        for field, label in required_fields.items():
                            if field not in st.session_state.irb_form_data or not st.session_state.irb_form_data[field]:
                                missing_fields.append(label)

                        if missing_fields:
                            st.error(f"Please complete all required fields before submitting")
                        else:
                            try:
                                # Process submission
                                form_data = st.session_state.irb_form_data

                                # Include the list of collaborating institutions in the submission
                                collaborating_institutions = form_data.get("collaborating_institutions", [])
                                all_institutions = [form_data["institution_id"]] + collaborating_institutions

                                # Create a unified project description that includes all sections of the protocol
                                full_project_description = f"""
# {form_data['title']}

## Protocol Information
- Protocol Number: {form_data.get('protocol_number', '')}
- Version: {form_data.get('version_number', '1.0')}
- Date: {form_data.get('version_date', datetime.now().date())}
- IRB#: {form_data.get('irb_number', '')}

## 1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE
{form_data.get('background', '')}

### Study Rationale
{form_data.get('rationale', '')}

## 2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS
### Primary Objective and Endpoint
{form_data.get('primary_objective', '')}

### Secondary Objectives
{form_data.get('secondary_objectives', '')}

### Study Design
- Type: {form_data.get('study_type', '')}
- Setting: {form_data.get('study_setting', '')}

### Research Methodology
{form_data.get('methodology', '')}

## 3. STUDY POPULATION
### Participant Selection
{form_data.get('participant_selection', '')}

### Inclusion Criteria
{form_data.get('inclusion_criteria', '')}

### Exclusion Criteria
{form_data.get('exclusion_criteria', '')}

### Vulnerable Populations
{form_data.get('vulnerable_populations', '')}

## 4. STUDY PROCEDURES
### Data Sources
{form_data.get('data_sources', '')}

### Case Ascertainment
{form_data.get('case_ascertainment', '')}

### Variable Abstraction
{form_data.get('variable_abstraction', '')}

## 5. STATISTICAL CONSIDERATIONS
{form_data.get('statistical_methods', '')}

### Sample Size Determination
{form_data.get('sample_size', '')}

## 6. RISK-BENEFIT ASSESSMENT & ETHICAL CONSIDERATIONS
{form_data.get('risks_and_benefits', '')}

### Consent Process
{form_data.get('consent_process', '')}

### Data Safety and Privacy
{form_data.get('data_safety_plan', '')}

## 7. TIMELINE AND REFERENCES
### Timeline
{form_data.get('timeline', '')}

### References
{form_data.get('references', '')}
"""

                                submission_id = submit_irb_application(
                                    title=form_data['title'],
                                    pi_id=st.session_state.user_id,
                                    institution_id=form_data['institution_id'],
                                    project_description=full_project_description,
                                    methodology=form_data['methodology'],
                                    risks_and_benefits=form_data['risks_and_benefits'],
                                    participant_selection=form_data['participant_selection'],
                                    consent_process=form_data['consent_process'],
                                    data_safety_plan=form_data['data_safety_plan'],
                                    collaborating_institutions=all_institutions
                                )

                                st.success(f"""
                                    IRB application submitted successfully!
                                    Submission ID: {submission_id}

                                    Your application will be reviewed by {len(all_institutions)} institution(s).
                                """)

                                # Reset form after successful submission
                                update_form_state("reset")
                                st.experimental_rerun()

                            except Exception as e:
                                st.error(f"Error submitting IRB application: {str(e)}")
                else:
                    next_button = st.form_submit_button("Next Step →")
                    if next_button:
                        update_form_state("next")
                        st.experimental_rerun()

            with col2:
                if st.form_submit_button("Save Draft"):
                    st.success("Your progress has been saved. You can continue later.")

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("My IRB Submissions")

        # Get user's submissions
        try:
            submissions = get_irb_submissions(pi_id=st.session_state.user_id)

            if not submissions:
                st.info("You haven't made any IRB submissions yet.")
            else:
                for sub in submissions:
                    status_class = f"status-{sub['status']}"

                    st.markdown(f"""
                    <div class="submission-card">
                        <h3>{sub['title']}</h3>
                        <p>Status: <span class="{status_class}">{sub['status'].upper()}</span></p>
                        <p>Submitted: {sub['submitted_at'].strftime('%Y-%m-%d %H:%M')}</p>
                        <p>Institution: {sub['institution_name']}</p>
                        <p>Reviews: {sub['review_count']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("View Details"):
                        st.subheader("Project Description")
                        st.write(sub['project_description'])

                        st.subheader("Methodology")
                        st.write(sub['methodology'])

                        # Show multi-institutional approval status
                        st.subheader("Institutional Approvals")
                        approvals = get_submission_approvals(sub['id'])

                        if approvals:
                            cols = st.columns(3)
                            for i, approval in enumerate(approvals):
                                with cols[i % 3]:
                                    status_badge_class = f"approval-{approval['status']}"

                                    st.markdown(f"""
                                    <div class="approval-card">
                                        <strong>{approval['institution_name']}</strong><br>
                                        <span class="approval-badge {status_badge_class}">
                                            {approval['status'].upper()}
                                        </span><br>
                                        <small>
                                            {f"Reviewed by: {approval['reviewer_name']}" if approval['reviewer_name'] else "Not yet reviewed"}
                                        </small>
                                    </div>
                                    """, unsafe_allow_html=True)

                        else:
                            st.info("No institutional approvals found.")

                        st.subheader("Status History")
                        if sub['status'] == 'pending':
                            st.info("Your submission is under review.")
                        elif sub['status'] == 'approved':
                            st.success("Your submission has been approved by all required institutions!")
                        elif sub['status'] == 'rejected':
                            st.error("Your submission was not approved by at least one institution.")

        except Exception as e:
            st.error(f"Error loading submissions: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("Review IRB Applications")

        # In a real application, you would check if user is an IRB reviewer
        # For demo, we'll allow all users to review
        try:
            all_submissions = get_irb_submissions()

            if not all_submissions:
                st.info("No IRB submissions to review.")
            else:
                for sub in all_submissions:
                    if sub['principal_investigator_id'] == st.session_state.user_id:
                        continue  # Skip own submissions

                    status_class = f"status-{sub['status']}"

                    st.markdown(f"""
                    <div class="submission-card">
                        <h3>{sub['title']}</h3>
                        <p>Status: <span class="{status_class}">{sub['status'].upper()}</span></p>
                        <p>PI: {sub['pi_name']}</p>
                        <p>Institution: {sub['institution_name']}</p>
                        <p>Submitted: {sub['submitted_at'].strftime('%Y-%m-%d %H:%M')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("Review Application"):
                        st.subheader("Project Details")
                        st.write(sub['project_description'])

                        st.subheader("Methodology")
                        st.write(sub['methodology'])

                        st.markdown('<div class="review-form">', unsafe_allow_html=True)
                        with st.form(f"review_form_{sub['id']}"):
                            review_type = st.selectbox(
                                "Review Type",
                                ["Initial Review", "Continuing Review", "Amendment Review"],
                                key=f"review_type_{sub['id']}"
                            )

                            comments = st.text_area(
                                "Review Comments",
                                key=f"comments_{sub['id']}"
                            )

                            decision = st.selectbox(
                                "Decision",
                                ["pending", "approved", "rejected"],
                                key=f"decision_{sub['id']}"
                            )

                            if st.form_submit_button("Submit Review"):
                                try:
                                    review_id = submit_irb_review(
                                        submission_id=sub['id'],
                                        reviewer_id=st.session_state.user_id,
                                        review_type=review_type,
                                        comments=comments,
                                        decision=decision
                                    )

                                    st.success("Review submitted successfully!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Error submitting review: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading submissions for review: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="irb-section">', unsafe_allow_html=True)
        st.header("Institutional Approvals")

        # For demo purposes, create a default institution assignment
        try:
            # Try to get the institution from user's profile
            conn = get_database_connection()
            cur = conn.cursor()
            cur.execute("SELECT institution FROM users WHERE id = %s", (st.session_state.user_id,))
            result = cur.fetchone()

            # If user doesn't have an institution in their profile, assign a default one
            if result is None or result[0] is None:
                # Get first institution for demo purposes
                institutions_df = get_institutions()
                if not institutions_df.empty:
                    user_institution = institutions_df.iloc[0]['name']
                    # For demo, we don't update the user record, just use the institution name
                else:
                    user_institution = "Demo Institution"
            else:
                user_institution = result[0]

            conn.close()

            # Get institution ID for user's institution
            institutions_df = get_institutions()
            institution_matches = institutions_df[institutions_df['name'] == user_institution]

            if institution_matches.empty:
                # If institution not found, use the first one for demo
                if not institutions_df.empty:
                    user_institution = institutions_df.iloc[0]['name']
                    user_institution_id = institutions_df.iloc[0]['id']
                else:
                    st.warning("No institutions found in the system. Please add some first.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return
            else:
                user_institution_id = institution_matches.iloc[0]['id']

            # Get submissions that need approval from this institution
            st.subheader(f"Applications Requiring {user_institution} Approval")

            conn = get_database_connection()
            query = """
                SELECT 
                    s.id, s.title, s.status as submission_status, 
                    u.username as pi_name,
                    ia.id as approval_id, ia.status as approval_status,
                    ia.reviewer_id, ia.comments, ia.approval_date
                FROM irb_submissions s
                JOIN users u ON s.principal_investigator_id = u.id
                JOIN irb_institutional_approvals ia ON s.id = ia.submission_id
                WHERE ia.institution_id = %s
                ORDER BY s.submitted_at DESC
            """
            approvals_df = pd.read_sql(query, conn, params=(user_institution_id,))
            conn.close()

            if approvals_df.empty:
                st.info(f"No applications require approval from {user_institution}.")
            else:
                for _, row in approvals_df.iterrows():
                    approval_status_class = f"status-{row['approval_status']}"

                    st.markdown(f"""
                    <div class="submission-card">
                        <h3>{row['title']}</h3>
                        <p>Principal Investigator: {row['pi_name']}</p>
                        <p>Approval Status: <span class="{approval_status_class}">{row['approval_status'].upper()}</span></p>
                        {f"<p>Reviewed on: {row['approval_date']}</p>" if pd.notna(row['approval_date']) else ""}
                    </div>
                    """, unsafe_allow_html=True)

                    # Only show approval form if not already approved/rejected by this user
                    if (pd.isna(row['reviewer_id']) or row['approval_status'] == 'pending'):
                        with st.expander("Review for Institutional Approval"):
                            # Get full submission details for review
                            conn = get_database_connection()
                            cur = conn.cursor(cursor_factory=RealDictCursor)
                            cur.execute("""
                                SELECT * FROM irb_submissions WHERE id = %s
                            """, (row['id'],))
                            submission = cur.fetchone()
                            conn.close()

                            if submission:
                                st.markdown(f"#### Review Request from {row['pi_name']}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**Project Description**")
                                    st.write(submission['project_description'])
                                with col2:
                                    st.markdown("**Methodology**")
                                    st.write(submission['methodology'])

                                st.markdown("**Risk Assessment**")
                                st.write(submission['risks_and_benefits'])

                                with st.form(f"approval_form_{row['approval_id']}"):
                                    comments = st.text_area(
                                        "Institutional Review Comments",
                                        help="Provide feedback from your institution's perspective"
                                    )

                                    status = st.radio(
                                        "Institutional Decision",
                                        ["approved", "rejected", "pending"],
                                        index=2
                                    )

                                    if st.form_submit_button("Submit Institutional Decision"):
                                        try:
                                            updated = update_institutional_approval(
                                                approval_id=row['approval_id'],
                                                reviewer_id=st.session_state.user_id,
                                                status=status,
                                                comments=comments
                                            )

                                            if updated:
                                                st.success(f"Institutional review submitted successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update approval status.")
                                        except Exception as e:
                                            st.error(f"Error updating institutional approval: {str(e)}")

        except Exception as e:
            st.error(f"Error loading institutional approvals: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    irb_portal()

if __name__ == "__main__":
    main()