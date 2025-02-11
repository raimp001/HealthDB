import streamlit as st
from database import (
    get_database_connection,
    submit_irb_application,
    get_irb_submissions,
    submit_irb_review
)
import pandas as pd
from datetime import datetime

def get_institutions():
    """Get list of participating institutions."""
    conn = get_database_connection()
    query = "SELECT id, name FROM institutions ORDER BY name;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def irb_portal():
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to access the IRB portal.")
        return

    st.title("IRB Submission Portal")
    
    # Tabs for different IRB portal sections
    tab1, tab2, tab3 = st.tabs([
        "Submit IRB Application",
        "My Submissions",
        "Review Applications"
    ])
    
    with tab1:
        st.header("New IRB Submission")
        
        # Get institutions for dropdown
        institutions = get_institutions()
        if len(institutions) == 0:
            st.error("No institutions are currently registered in the system.")
            return
            
        # IRB Submission Form
        with st.form("irb_submission_form"):
            st.subheader("Project Information")
            
            title = st.text_input("Project Title")
            institution_id = st.selectbox(
                "Institution",
                options=institutions['id'].tolist(),
                format_func=lambda x: institutions[
                    institutions['id'] == x
                ]['name'].iloc[0]
            )
            
            st.subheader("Project Details")
            project_description = st.text_area(
                "Project Description",
                help="Provide a comprehensive overview of your research project"
            )
            
            methodology = st.text_area(
                "Research Methodology",
                help="Describe your research methods, including data collection procedures"
            )
            
            risks_and_benefits = st.text_area(
                "Risks and Benefits",
                help="Detail potential risks to participants and expected benefits of the research"
            )
            
            participant_selection = st.text_area(
                "Participant Selection",
                help="Describe your participant selection criteria and recruitment process"
            )
            
            consent_process = st.text_area(
                "Consent Process",
                help="Explain how you will obtain informed consent from participants"
            )
            
            data_safety_plan = st.text_area(
                "Data Safety and Privacy",
                help="Describe how you will protect participant data and maintain confidentiality"
            )
            
            submitted = st.form_submit_button("Submit IRB Application")
            
            if submitted:
                try:
                    submission_id = submit_irb_application(
                        title=title,
                        pi_id=st.session_state.user_id,
                        institution_id=institution_id,
                        project_description=project_description,
                        methodology=methodology,
                        risks_and_benefits=risks_and_benefits,
                        participant_selection=participant_selection,
                        consent_process=consent_process,
                        data_safety_plan=data_safety_plan
                    )
                    
                    st.success(f"""
                        IRB application submitted successfully!
                        Submission ID: {submission_id}
                    """)
                    
                except Exception as e:
                    st.error(f"Error submitting IRB application: {str(e)}")
    
    with tab2:
        st.header("My IRB Submissions")
        
        # Get user's submissions
        try:
            submissions = get_irb_submissions(pi_id=st.session_state.user_id)
            
            if not submissions:
                st.info("You haven't made any IRB submissions yet.")
            else:
                for sub in submissions:
                    with st.expander(
                        f"{sub['title']} - Status: {sub['status'].upper()}"
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"Submitted: {sub['submitted_at']}")
                            st.write(f"Institution: {sub['institution_name']}")
                        with col2:
                            st.write(f"Reviews: {sub['review_count']}")
                            st.write(
                                f"Last Updated: {sub['last_updated_at']}"
                            )
                        
                        st.subheader("Project Description")
                        st.write(sub['project_description'])
                        
                        if sub['status'] == 'pending':
                            st.info("Your submission is under review.")
                        elif sub['status'] == 'approved':
                            st.success("Your submission has been approved!")
                        elif sub['status'] == 'rejected':
                            st.error("Your submission was not approved.")
                            
        except Exception as e:
            st.error(f"Error loading submissions: {str(e)}")
    
    with tab3:
        st.header("Review IRB Applications")
        
        # In a real application, you would check if user is an IRB reviewer
        # For now, we'll assume all users can review
        try:
            all_submissions = get_irb_submissions()
            
            if not all_submissions:
                st.info("No IRB submissions to review.")
            else:
                for sub in all_submissions:
                    if sub['principal_investigator_id'] == st.session_state.user_id:
                        continue  # Skip own submissions
                        
                    with st.expander(
                        f"Review: {sub['title']} ({sub['institution_name']})"
                    ):
                        st.write(f"PI: {sub['pi_name']}")
                        st.write(f"Submitted: {sub['submitted_at']}")
                        st.write(f"Status: {sub['status'].upper()}")
                        
                        st.subheader("Project Details")
                        st.write(sub['project_description'])
                        
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
                        
        except Exception as e:
            st.error(f"Error loading submissions for review: {str(e)}")

if __name__ == "__main__":
    irb_portal()
