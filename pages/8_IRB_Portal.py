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

        # IRB Submission Form - Updated with protocol template structure
        with st.form("irb_submission_form"):
            st.markdown('<div class="form-section protocol-header">', unsafe_allow_html=True)
            st.subheader("IRB Protocol Information")

            # Protocol Header Table
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Study Title", 
                    help="Full title of the research project")
                protocol_number = st.text_input("Protocol Number", 
                    help="The unique identifier for this protocol")
                version_number = st.text_input("Version Number", 
                    placeholder="1.0")

            with col2:
                version_date = st.date_input("Version Date", 
                    help="Date of this protocol version")
                irb_number = st.text_input("IRB#", 
                    help="Will be assigned after submission if approved")

            # Principal Investigator and Institution
            st.subheader("Principal Investigator Information")

            institution_id = st.selectbox(
                "Primary Institution",
                options=institutions['id'].tolist(),
                format_func=lambda x: institutions[
                    institutions['id'] == x
                ]['name'].iloc[0]
            )

            # Multi-institutional selection
            st.subheader("Collaborating Institutions")
            st.info("Select additional institutions that need to approve this IRB submission")

            # Create a multi-select for additional institutions
            other_institutions = institutions[institutions['id'] != institution_id]
            collaborating_institutions = st.multiselect(
                "Collaborating Institutions (Optional)",
                options=other_institutions['id'].tolist(),
                format_func=lambda x: other_institutions[
                    other_institutions['id'] == x
                ]['name'].iloc[0],
                help="Select institutions that are collaborating on this research project and need to provide IRB approval"
            )

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

            # Background and Rationale
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE")

            background = st.text_area(
                "Background Information",
                help="Provide background information on the research area, including description of the condition/issue, current state of knowledge, and relevant previous findings",
                height=150
            )

            rationale = st.text_area(
                "Study Rationale",
                help="Explain the scientific rationale for conducting this specific study, including purpose and potential contributions",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Study Design and Objectives
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS")

            primary_objective = st.text_area(
                "Primary Objective and Endpoint",
                help="State the primary objective of the study and the main outcome measure(s)",
                height=100
            )

            secondary_objectives = st.text_area(
                "Secondary Objectives (Optional)",
                help="List additional objectives of the study, if applicable",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                study_type = st.selectbox(
                    "Study Type",
                    options=[
                        "Retrospective cohort study", 
                        "Prospective cohort", 
                        "Randomized controlled trial",
                        "Case-control study",
                        "Cross-sectional study",
                        "Observational study",
                        "Other"
                    ]
                )

            with col2:
                study_setting = st.text_input(
                    "Study Setting",
                    help="Describe where the study will be conducted"
                )

            methodology = st.text_area(
                "Research Methodology",
                help="Describe your research methods, including data collection procedures",
                height=150
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Study Population
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("3. STUDY POPULATION")

            participant_selection = st.text_area(
                "Participant Selection",
                help="Describe your participant selection criteria and recruitment process",
                height=100
            )

            inclusion_criteria = st.text_area(
                "Inclusion Criteria",
                help="List criteria that define who will be included in your study",
                height=100
            )

            exclusion_criteria = st.text_area(
                "Exclusion Criteria",
                help="List criteria that would exclude an individual from participating",
                height=100
            )

            vulnerable_populations = st.text_area(
                "Vulnerable Populations",
                help="State whether vulnerable populations will be included and provide justification if applicable",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Study Procedures
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("4. STUDY PROCEDURES")

            data_sources = st.text_area(
                "Data Sources",
                help="Specify the data sources that will be used",
                height=100
            )

            case_ascertainment = st.text_area(
                "Case Ascertainment",
                help="Explain how cases will be identified and confirmed",
                height=100
            )

            variable_abstraction = st.text_area(
                "Variable Abstraction",
                help="List the variables to be collected (demographics, clinical characteristics, laboratory data, outcome measures, etc.)",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Statistical Considerations
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("5. STATISTICAL CONSIDERATIONS")

            statistical_methods = st.text_area(
                "Statistical Methods",
                help="Provide information on descriptive analyses, primary/secondary analyses, and statistical software to be used",
                height=100
            )

            sample_size = st.text_area(
                "Sample Size Determination",
                help="Explain how the sample size was determined, including power calculations if applicable",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Risk and Ethical Considerations
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("6. RISK-BENEFIT ASSESSMENT & ETHICAL CONSIDERATIONS")

            risks_and_benefits = st.text_area(
                "Risks and Benefits",
                help="Detail potential risks to participants and expected benefits of the research",
                height=100
            )

            consent_process = st.text_area(
                "Consent Process",
                help="Explain how you will obtain informed consent from participants",
                height=100
            )

            data_safety_plan = st.text_area(
                "Data Safety and Privacy",
                help="Describe how you will protect participant data and maintain confidentiality",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Timeline and References
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.subheader("7. TIMELINE AND REFERENCES")

            timeline = st.text_area(
                "Project Timeline",
                help="Present a timeline of project activities and expected completion dates",
                height=100
            )

            references = st.text_area(
                "References",
                help="List all references cited in the protocol",
                height=100
            )
            st.markdown('</div>', unsafe_allow_html=True)

            submitted = st.form_submit_button("Submit IRB Application")

            if submitted:
                try:
                    # Include the list of collaborating institutions in the submission
                    all_institutions = [institution_id] + collaborating_institutions

                    # Create a unified project description that includes all sections of the protocol
                    full_project_description = f"""
# {title}

## Protocol Information
- Protocol Number: {protocol_number}
- Version: {version_number}
- Date: {version_date}
- IRB#: {irb_number}

## 1. BACKGROUND INFORMATION AND SCIENTIFIC RATIONALE
{background}

### Study Rationale
{rationale}

## 2. STUDY DESIGN, OBJECTIVES AND ENDPOINTS
### Primary Objective and Endpoint
{primary_objective}

### Secondary Objectives
{secondary_objectives}

### Study Design
- Type: {study_type}
- Setting: {study_setting}

### Research Methodology
{methodology}

## 3. STUDY POPULATION
### Participant Selection
{participant_selection}

### Inclusion Criteria
{inclusion_criteria}

### Exclusion Criteria
{exclusion_criteria}

### Vulnerable Populations
{vulnerable_populations}

## 4. STUDY PROCEDURES
### Data Sources
{data_sources}

### Case Ascertainment
{case_ascertainment}

### Variable Abstraction
{variable_abstraction}

## 5. STATISTICAL CONSIDERATIONS
{statistical_methods}

### Sample Size Determination
{sample_size}

## 6. RISK-BENEFIT ASSESSMENT & ETHICAL CONSIDERATIONS
{risks_and_benefits}

### Consent Process
{consent_process}

### Data Safety and Privacy
{data_safety_plan}

## 7. TIMELINE AND REFERENCES
### Timeline
{timeline}

### References
{references}
"""

                    submission_id = submit_irb_application(
                        title=title,
                        pi_id=st.session_state.user_id,
                        institution_id=institution_id,
                        project_description=full_project_description,
                        methodology=methodology,
                        risks_and_benefits=risks_and_benefits,
                        participant_selection=participant_selection,
                        consent_process=consent_process,
                        data_safety_plan=data_safety_plan,
                        collaborating_institutions=all_institutions
                    )

                    st.success(f"""
                        IRB application submitted successfully!
                        Submission ID: {submission_id}

                        Your application will be reviewed by {len(all_institutions)} institution(s).
                    """)

                except Exception as e:
                    st.error(f"Error submitting IRB application: {str(e)}")
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
                                            st.error(f"Error submitting institutional review: {str(e)}")
                            else:
                                st.error("Could not retrieve submission details.")

                    else:
                        # Show previous review details
                        with st.expander("View Approval Details"):
                            st.info(f"This submission has already been reviewed with status: {row['approval_status'].upper()}")

                            if pd.notna(row['comments']):
                                st.markdown("**Review Comments:**")
                                st.write(row['comments'])

                            # Add option to update the status if needed
                            if st.button(f"Update approval status for #{row['id']}", key=f"update_{row['approval_id']}"):
                                st.session_state[f"show_update_form_{row['approval_id']}"] = True

                            if st.session_state.get(f"show_update_form_{row['approval_id']}", False):
                                with st.form(f"update_form_{row['approval_id']}"):
                                    new_comments = st.text_area(
                                        "Updated Comments",
                                        value=row['comments'] if pd.notna(row['comments']) else "",
                                        key=f"update_comments_{row['approval_id']}"
                                    )

                                    new_status = st.radio(
                                        "Updated Decision",
                                        ["approved", "rejected", "pending"],
                                        index=0 if row['approval_status'] == 'approved' else 
                                              1 if row['approval_status'] == 'rejected' else 2,
                                        key=f"update_status_{row['approval_id']}"
                                    )

                                    if st.form_submit_button("Update Approval"):
                                        try:
                                            updated = update_institutional_approval(
                                                approval_id=row['approval_id'],
                                                reviewer_id=st.session_state.user_id,
                                                status=new_status,
                                                comments=new_comments
                                            )

                                            if updated:
                                                st.success("Approval status updated successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update approval status.")
                                        except Exception as e:
                                            st.error(f"Error updating approval status: {str(e)}")

        except Exception as e:
            st.error(f"Error loading institutional approvals: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    irb_portal()