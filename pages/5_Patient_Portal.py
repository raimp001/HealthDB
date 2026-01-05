"""
Patient Portal Page
Allows patients to manage consent, view their contribution, and earn rewards
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import random
from components.navigation import render_navigation

# Page config
st.set_page_config(
    page_title="Patient Portal - HealthDB",
    page_icon="💜",
    layout="wide"
)

# Custom CSS with modern patient-friendly design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    .patient-hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .patient-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 60%;
        height: 200%;
        background: rgba(255,255,255,0.1);
        transform: rotate(30deg);
        pointer-events: none;
    }
    .patient-hero h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .patient-hero p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .impact-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        height: 100%;
    }
    .impact-card h3 {
        color: #1f2937;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .impact-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .impact-label {
        color: #6b7280;
        font-size: 0.85rem;
    }
    
    .consent-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    .consent-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .consent-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .consent-active {
        background: #d1fae5;
        color: #059669;
    }
    .consent-pending {
        background: #fef3c7;
        color: #d97706;
    }
    
    .reward-badge {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .activity-item {
        display: flex;
        align-items: flex-start;
        padding: 1rem 0;
        border-bottom: 1px solid #f3f4f6;
    }
    .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        font-size: 1.2rem;
    }
    .activity-icon.data { background: #dbeafe; }
    .activity-icon.reward { background: #fef3c7; }
    .activity-icon.survey { background: #d1fae5; }
    
    .research-study {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .research-study h4 {
        color: #166534;
        margin-bottom: 0.5rem;
    }
    
    .tab-content {
        padding: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

render_navigation()

# Check if patient is logged in (demo mode)
if 'patient_logged_in' not in st.session_state:
    st.session_state.patient_logged_in = True
    st.session_state.patient_name = "Sarah M."
    st.session_state.patient_points = 450
    st.session_state.patient_level = "Active Contributor"

# Hero section
st.markdown(f"""
<div class="patient-hero">
    <h1>Welcome back, {st.session_state.patient_name} 💜</h1>
    <p>Your data is making a difference in cancer research</p>
</div>
""", unsafe_allow_html=True)

# Impact metrics
st.subheader("Your Impact")

impact_cols = st.columns(4)

with impact_cols[0]:
    st.markdown("""
    <div class="impact-card">
        <h3>🔬 Studies Supported</h3>
        <div class="impact-value">12</div>
        <div class="impact-label">Active research projects</div>
    </div>
    """, unsafe_allow_html=True)

with impact_cols[1]:
    st.markdown("""
    <div class="impact-card">
        <h3>👥 Fellow Patients</h3>
        <div class="impact-value">847</div>
        <div class="impact-label">In your condition community</div>
    </div>
    """, unsafe_allow_html=True)

with impact_cols[2]:
    st.markdown(f"""
    <div class="impact-card">
        <h3>⭐ Your Points</h3>
        <div class="impact-value">{st.session_state.patient_points}</div>
        <div class="impact-label">${st.session_state.patient_points * 0.01:.2f} value</div>
    </div>
    """, unsafe_allow_html=True)

with impact_cols[3]:
    st.markdown(f"""
    <div class="impact-card">
        <h3>🏆 Status</h3>
        <div class="impact-value" style="font-size: 1.5rem;">{st.session_state.patient_level}</div>
        <div class="impact-label">50 more points to Champion!</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Dashboard", 
    "📋 My Consents", 
    "🎁 Rewards",
    "📊 My Data",
    "🔬 Research Studies"
])

with tab1:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Recent Activity")
        
        activities = [
            {"icon": "🔬", "type": "data", "text": "Your data contributed to a lymphoma treatment study", "time": "2 hours ago", "points": "+25"},
            {"icon": "🎁", "type": "reward", "text": "Earned points for completing health survey", "time": "Yesterday", "points": "+15"},
            {"icon": "📋", "type": "survey", "text": "New survey available: Quality of Life Assessment", "time": "2 days ago", "points": ""},
            {"icon": "🔬", "type": "data", "text": "Data accessed by Stanford Cancer Research", "time": "3 days ago", "points": "+50"},
            {"icon": "✅", "type": "survey", "text": "Consent renewed for General Research", "time": "1 week ago", "points": "+25"},
        ]
        
        for activity in activities:
            st.markdown(f"""
            <div class="activity-item">
                <div class="activity-icon {activity['type']}">{activity['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 500;">{activity['text']}</div>
                    <div style="color: #6b7280; font-size: 0.85rem;">{activity['time']}</div>
                </div>
                <div style="color: #059669; font-weight: 600;">{activity['points']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        st.subheader("Upcoming")
        
        st.markdown("""
        <div class="consent-card">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">📋</span>
                <strong>Monthly Survey</strong>
            </div>
            <p style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.5rem;">
                5-minute quality of life check-in
            </p>
            <div style="color: #6366f1; font-weight: 600;">+15 points</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="consent-card">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">🔔</span>
                <strong>Consent Renewal</strong>
            </div>
            <p style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.5rem;">
                Your research consent expires in 30 days
            </p>
            <div style="color: #d97706; font-weight: 600;">Action needed</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.subheader("Your Contribution")
        
        # Contribution chart
        contribution_data = pd.DataFrame({
            'Month': ['Sep', 'Oct', 'Nov', 'Dec', 'Jan'],
            'Studies': [2, 4, 3, 5, 4]
        })
        
        fig = px.area(
            contribution_data,
            x='Month',
            y='Studies',
            title="Studies Your Data Supported",
            color_discrete_sequence=['#8b5cf6']
        )
        fig.update_layout(
            height=200,
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Manage Your Consents")
    
    st.markdown("""
    <p style="color: #6b7280; margin-bottom: 1.5rem;">
        Control how your data is used in research. You can withdraw consent at any time.
    </p>
    """, unsafe_allow_html=True)
    
    consents = [
        {
            "title": "General Research Consent",
            "description": "Allow your de-identified data to be used in academic research studies",
            "status": "active",
            "date": "Jan 15, 2025",
            "expires": "Jan 15, 2026"
        },
        {
            "title": "Commercial Research Consent",
            "description": "Allow pharmaceutical companies to access your data for drug development",
            "status": "active",
            "date": "Jan 15, 2025",
            "expires": "Jan 15, 2026"
        },
        {
            "title": "Genetic Research Consent",
            "description": "Allow genomic/molecular data to be used in genetic studies",
            "status": "pending",
            "date": "",
            "expires": ""
        },
        {
            "title": "Future Contact Consent",
            "description": "Allow researchers to contact you about relevant clinical trials",
            "status": "active",
            "date": "Jan 15, 2025",
            "expires": "Jan 15, 2026"
        }
    ]
    
    for consent in consents:
        status_class = "consent-active" if consent["status"] == "active" else "consent-pending"
        status_text = "Active" if consent["status"] == "active" else "Not Signed"
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="consent-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0;">{consent['title']}</h4>
                        <p style="color: #6b7280; margin: 0 0 0.5rem 0; font-size: 0.9rem;">{consent['description']}</p>
                        {'<p style="font-size: 0.8rem; color: #9ca3af;">Signed: ' + consent['date'] + ' · Expires: ' + consent['expires'] + '</p>' if consent['status'] == 'active' else ''}
                    </div>
                    <span class="consent-status {status_class}">{status_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if consent["status"] == "active":
                if st.button("Manage", key=f"manage_{consent['title']}", use_container_width=True):
                    st.info("Opening consent management...")
            else:
                if st.button("Sign Now", key=f"sign_{consent['title']}", type="primary", use_container_width=True):
                    st.success("Opening consent form...")

with tab3:
    st.subheader("Your Rewards")
    
    col_balance, col_redeem = st.columns([1, 1])
    
    with col_balance:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); 
                    padding: 2rem; border-radius: 1rem; color: white; text-align: center;">
            <h3 style="margin: 0; opacity: 0.9;">Available Balance</h3>
            <div style="font-size: 3rem; font-weight: 700; margin: 0.5rem 0;">{st.session_state.patient_points} pts</div>
            <div style="font-size: 1.25rem; opacity: 0.9;">${st.session_state.patient_points * 0.01:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_redeem:
        st.markdown("""
        <div class="impact-card">
            <h3 style="margin-bottom: 1rem;">Redeem Your Points</h3>
        </div>
        """, unsafe_allow_html=True)
        
        redemption_option = st.selectbox(
            "Choose redemption method",
            ["Amazon Gift Card", "PayPal Cash", "Donate to Cancer Research", "Healthcare Credits"]
        )
        
        redemption_amount = st.slider(
            "Points to redeem",
            min_value=100,
            max_value=st.session_state.patient_points,
            value=min(200, st.session_state.patient_points),
            step=50
        )
        
        st.write(f"Value: ${redemption_amount * 0.01:.2f}")
        
        if st.button("Redeem Now", type="primary", use_container_width=True):
            st.success(f"Successfully redeemed {redemption_amount} points for {redemption_option}!")
    
    st.markdown("---")
    
    st.subheader("Earning History")
    
    earning_history = pd.DataFrame({
        'Date': ['Jan 3, 2026', 'Jan 2, 2026', 'Dec 28, 2025', 'Dec 20, 2025', 'Dec 15, 2025'],
        'Activity': ['Data accessed by researcher', 'Completed survey', 'Data contributed to study', 'Profile verification bonus', 'Initial consent bonus'],
        'Points': [50, 15, 50, 100, 100],
    })
    
    st.dataframe(
        earning_history,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Points": st.column_config.NumberColumn(format="+%d pts")
        }
    )

with tab4:
    st.subheader("Your Health Data")
    
    st.info("🔒 Your data is de-identified and encrypted. Only you can see identifying information.")
    
    # Data summary
    data_categories = [
        {"icon": "📋", "name": "Demographics", "records": 1, "last_updated": "Jan 1, 2026"},
        {"icon": "🩺", "name": "Diagnoses", "records": 3, "last_updated": "Dec 15, 2025"},
        {"icon": "💊", "name": "Treatments", "records": 8, "last_updated": "Jan 2, 2026"},
        {"icon": "🧬", "name": "Lab Results", "records": 45, "last_updated": "Jan 3, 2026"},
        {"icon": "🔬", "name": "Molecular/Genetic", "records": 2, "last_updated": "Nov 10, 2025"},
        {"icon": "📊", "name": "Survey Responses", "records": 12, "last_updated": "Dec 28, 2025"},
    ]
    
    data_cols = st.columns(3)
    
    for i, cat in enumerate(data_categories):
        with data_cols[i % 3]:
            st.markdown(f"""
            <div class="consent-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{cat['icon']}</div>
                <h4 style="margin: 0;">{cat['name']}</h4>
                <div style="color: #6366f1; font-size: 1.5rem; font-weight: 700;">{cat['records']}</div>
                <div style="color: #9ca3af; font-size: 0.8rem;">records</div>
                <div style="color: #6b7280; font-size: 0.8rem; margin-top: 0.5rem;">Updated: {cat['last_updated']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("Data Access Log")
    st.markdown("See who has accessed your data")
    
    access_log = pd.DataFrame({
        'Date': ['Jan 3, 2026', 'Dec 28, 2025', 'Dec 15, 2025', 'Dec 1, 2025'],
        'Researcher/Institution': ['Stanford Cancer Center', 'NIH Lymphoma Study', 'Mayo Clinic Research', 'Academic Consortium'],
        'Data Type': ['Treatment outcomes', 'All de-identified', 'Lab results', 'Demographics'],
        'Purpose': ['Treatment optimization study', 'Longitudinal outcomes research', 'Biomarker analysis', 'Epidemiology study'],
    })
    
    st.dataframe(access_log, hide_index=True, use_container_width=True)

with tab5:
    st.subheader("Research Studies")
    st.markdown("Studies using data from patients like you")
    
    studies = [
        {
            "title": "Novel CAR-T Therapy Outcomes in Relapsed Lymphoma",
            "institution": "Stanford Cancer Center",
            "status": "Active",
            "participants": 234,
            "your_data": True
        },
        {
            "title": "Biomarker Discovery for Treatment Response Prediction",
            "institution": "NIH / National Cancer Institute",
            "status": "Recruiting",
            "participants": 567,
            "your_data": True
        },
        {
            "title": "Quality of Life in Long-term Survivors",
            "institution": "Mayo Clinic",
            "status": "Active",
            "participants": 1203,
            "your_data": False
        }
    ]
    
    for study in studies:
        badge = "🌟 Your data is contributing!" if study["your_data"] else ""
        
        st.markdown(f"""
        <div class="research-study">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4>{study['title']}</h4>
                    <p style="color: #166534; margin: 0.25rem 0;">{study['institution']}</p>
                    <p style="color: #6b7280; font-size: 0.9rem; margin: 0.5rem 0;">
                        {study['participants']} participants · Status: {study['status']}
                    </p>
                </div>
                <div style="text-align: right;">
                    {f'<div style="background: #fef3c7; color: #92400e; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">{badge}</div>' if study["your_data"] else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("Clinical Trial Matches")
    st.markdown("Based on your profile, you may be eligible for these trials")
    
    trials = [
        {
            "title": "Phase II Study of Novel Immunotherapy Combination",
            "location": "Multiple locations",
            "phase": "Phase II",
            "match_score": 92
        },
        {
            "title": "CAR-T with Maintenance Therapy Trial",
            "location": "Boston, MA",
            "phase": "Phase III",
            "match_score": 85
        }
    ]
    
    for trial in trials:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="consent-card">
                <h4 style="margin: 0 0 0.25rem 0;">{trial['title']}</h4>
                <p style="color: #6b7280; margin: 0;">{trial['location']} · {trial['phase']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #059669;">{trial['match_score']}%</div>
                <div style="font-size: 0.75rem; color: #6b7280;">match</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Learn More", key=f"trial_{trial['title']}", use_container_width=True):
                st.info("Opening trial details...")

# Footer with helpful links
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>Questions? <a href="#">Contact Support</a> · <a href="#">Privacy Policy</a> · <a href="#">Terms of Service</a></p>
    <p style="font-size: 0.85rem;">Your privacy is our priority. All data is encrypted and de-identified.</p>
</div>
""", unsafe_allow_html=True)

