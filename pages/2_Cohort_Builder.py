"""
Cohort Builder Page
Interactive tool for building patient cohorts for retrospective studies
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
from components.navigation import render_navigation

# Page config
st.set_page_config(
    page_title="Cohort Builder - HealthDB",
    page_icon="🔬",
    layout="wide"
)

# Set up demo user
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
    st.session_state.username = "Demo User"

render_navigation()

# Custom CSS
st.markdown("""
<style>
    .cohort-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
    }
    .cohort-section h1 {
        color: white;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .cohort-section p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
    }
    .criteria-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stat-card {
        background: linear-gradient(135deg, #f6f9fc 0%, #eef2f7 100%);
        border-radius: 0.75rem;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a202c;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .filter-chip {
        display: inline-block;
        background: #e2e8f0;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    .filter-chip.active {
        background: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="cohort-section">
    <h1>🔬 Cohort Builder</h1>
    <p>Build patient cohorts for retrospective studies using powerful, flexible queries</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for cohort criteria
if 'cohort_criteria' not in st.session_state:
    st.session_state.cohort_criteria = []

# Main layout
col_filters, col_results = st.columns([1, 2])

with col_filters:
    st.subheader("📋 Define Cohort Criteria")
    
    # Cancer Type Selection
    st.markdown("**Cancer Type**")
    cancer_categories = {
        "Hematologic Malignancies": [
            "Acute Myeloid Leukemia",
            "Acute Lymphoblastic Leukemia",
            "Diffuse Large B-Cell Lymphoma",
            "Follicular Lymphoma",
            "Hodgkin Lymphoma",
            "Multiple Myeloma",
            "Chronic Lymphocytic Leukemia",
            "Myelodysplastic Syndrome"
        ],
        "Solid Tumors": [
            "Breast Cancer",
            "Lung Cancer (NSCLC)",
            "Lung Cancer (SCLC)",
            "Colorectal Cancer",
            "Pancreatic Cancer",
            "Prostate Cancer",
            "Ovarian Cancer",
            "Melanoma"
        ]
    }
    
    selected_category = st.selectbox(
        "Category",
        options=list(cancer_categories.keys())
    )
    
    selected_cancers = st.multiselect(
        "Specific Cancer Types",
        options=cancer_categories[selected_category],
        default=[]
    )
    
    st.markdown("---")
    
    # Demographics
    st.markdown("**Demographics**")
    
    age_range = st.slider(
        "Age at Diagnosis",
        min_value=0,
        max_value=100,
        value=(18, 80)
    )
    
    sex_filter = st.multiselect(
        "Sex",
        options=["Male", "Female", "Other"],
        default=["Male", "Female"]
    )
    
    st.markdown("---")
    
    # Clinical Staging
    st.markdown("**Disease Stage**")
    
    stages = st.multiselect(
        "Clinical Stage",
        options=["I", "II", "III", "IV", "IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IVA", "IVB"],
        default=[]
    )
    
    risk_groups = st.multiselect(
        "Risk Group",
        options=["Favorable", "Intermediate", "Adverse", "High-Risk", "Standard-Risk"],
        default=[]
    )
    
    st.markdown("---")
    
    # Molecular Features
    st.markdown("**Molecular/Genetic Features**")
    
    molecular_markers = {
        "AML": ["FLT3-ITD", "NPM1", "CEBPA", "IDH1", "IDH2", "TP53", "RUNX1", "ASXL1"],
        "ALL": ["BCR-ABL", "MLL", "ETV6-RUNX1", "Hyperdiploid", "Hypodiploid"],
        "Lymphoma": ["MYC", "BCL2", "BCL6", "Double-Hit", "Triple-Hit"],
        "Myeloma": ["t(4;14)", "t(14;16)", "del(17p)", "1q gain", "Hyperdiploid"],
        "Solid Tumor": ["EGFR", "ALK", "ROS1", "BRAF", "KRAS", "HER2", "PD-L1 High", "MSI-H"]
    }
    
    selected_marker_category = st.selectbox(
        "Marker Category",
        options=list(molecular_markers.keys())
    )
    
    selected_markers = st.multiselect(
        "Specific Markers",
        options=molecular_markers[selected_marker_category],
        default=[]
    )
    
    marker_status = st.radio(
        "Marker Status",
        options=["Present (Positive)", "Absent (Negative)", "Either"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Treatment History
    st.markdown("**Treatment History**")
    
    treatment_lines = st.select_slider(
        "Prior Lines of Therapy",
        options=["Any", "0 (Newly Diagnosed)", "1", "2", "3+"],
        value="Any"
    )
    
    treatment_types = st.multiselect(
        "Treatment Types Received",
        options=[
            "Chemotherapy",
            "Immunotherapy",
            "Targeted Therapy",
            "CAR-T Cell Therapy",
            "Stem Cell Transplant (Auto)",
            "Stem Cell Transplant (Allo)",
            "Radiation",
            "Surgery"
        ],
        default=[]
    )
    
    specific_regimens = st.text_input(
        "Specific Regimens (comma-separated)",
        placeholder="e.g., R-CHOP, Venetoclax, Pembrolizumab"
    )
    
    st.markdown("---")
    
    # Outcomes
    st.markdown("**Outcomes**")
    
    response_filter = st.multiselect(
        "Best Response Achieved",
        options=["CR", "CRu", "PR", "SD", "PD", "MRD Negative"],
        default=[]
    )
    
    relapse_filter = st.radio(
        "Relapse Status",
        options=["Any", "Had Relapse", "No Relapse", "Refractory"],
        horizontal=True
    )
    
    vital_status = st.multiselect(
        "Vital Status",
        options=["Alive", "Deceased", "Lost to Follow-up"],
        default=["Alive", "Deceased"]
    )
    
    st.markdown("---")
    
    # Date Range
    st.markdown("**Time Frame**")
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input(
            "Diagnosis From",
            value=date(2015, 1, 1)
        )
    with col_end:
        end_date = st.date_input(
            "Diagnosis To",
            value=date.today()
        )
    
    min_followup = st.number_input(
        "Minimum Follow-up (months)",
        min_value=0,
        max_value=120,
        value=6
    )

with col_results:
    # Query summary
    st.subheader("📊 Cohort Preview")
    
    # Build summary of criteria
    criteria_summary = []
    if selected_cancers:
        criteria_summary.append(f"Cancer: {', '.join(selected_cancers)}")
    if stages:
        criteria_summary.append(f"Stage: {', '.join(stages)}")
    if selected_markers:
        criteria_summary.append(f"Markers: {', '.join(selected_markers)}")
    if treatment_types:
        criteria_summary.append(f"Treatments: {', '.join(treatment_types)}")
    
    # Display active filters
    if criteria_summary:
        st.markdown("**Active Filters:**")
        filter_html = " ".join([f'<span class="filter-chip active">{c}</span>' for c in criteria_summary])
        st.markdown(f'<div>{filter_html}</div>', unsafe_allow_html=True)
    
    # Simulate cohort size (in production, this would query the database)
    import random
    random.seed(hash(str(selected_cancers) + str(stages) + str(age_range)))
    
    base_count = random.randint(500, 5000)
    if selected_cancers:
        base_count = int(base_count * 0.7)
    if stages:
        base_count = int(base_count * 0.6)
    if selected_markers:
        base_count = int(base_count * 0.4)
    if treatment_types:
        base_count = int(base_count * 0.5)
    
    cohort_size = max(50, base_count)
    
    # Statistics cards
    st.markdown("### Cohort Statistics")
    
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{cohort_size:,}</div>
            <div class="stat-label">Patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_cols[1]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{cohort_size * 8:,}</div>
            <div class="stat-label">Data Points</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_cols[2]:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{random.randint(12, 48)}</div>
            <div class="stat-label">Median F/U (mo)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_cols[3]:
        completeness = random.randint(75, 95)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{completeness}%</div>
            <div class="stat-label">Data Complete</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Visualization tabs
    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
        "Demographics", "Disease Characteristics", "Treatment Patterns", "Outcomes"
    ])
    
    with viz_tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Age distribution
            ages = [random.gauss(55, 15) for _ in range(cohort_size)]
            ages = [max(18, min(90, int(a))) for a in ages]
            
            fig_age = px.histogram(
                x=ages,
                nbins=20,
                title="Age Distribution at Diagnosis",
                labels={'x': 'Age', 'y': 'Count'},
                color_discrete_sequence=['#667eea']
            )
            fig_age.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            # Sex distribution
            sex_data = {
                'Sex': ['Male', 'Female', 'Other'],
                'Count': [int(cohort_size * 0.52), int(cohort_size * 0.47), int(cohort_size * 0.01)]
            }
            fig_sex = px.pie(
                sex_data,
                values='Count',
                names='Sex',
                title="Sex Distribution",
                color_discrete_sequence=['#667eea', '#764ba2', '#9F7AEA']
            )
            fig_sex.update_layout(height=300)
            st.plotly_chart(fig_sex, use_container_width=True)
    
    with viz_tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Stage distribution
            stage_data = pd.DataFrame({
                'Stage': ['I', 'II', 'III', 'IV'],
                'Patients': [
                    int(cohort_size * 0.15),
                    int(cohort_size * 0.25),
                    int(cohort_size * 0.35),
                    int(cohort_size * 0.25)
                ]
            })
            fig_stage = px.bar(
                stage_data,
                x='Stage',
                y='Patients',
                title="Stage Distribution",
                color='Patients',
                color_continuous_scale='Purples'
            )
            fig_stage.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_stage, use_container_width=True)
        
        with col2:
            # Risk group distribution
            risk_data = pd.DataFrame({
                'Risk Group': ['Favorable', 'Intermediate', 'Adverse'],
                'Patients': [
                    int(cohort_size * 0.25),
                    int(cohort_size * 0.45),
                    int(cohort_size * 0.30)
                ]
            })
            fig_risk = px.pie(
                risk_data,
                values='Patients',
                names='Risk Group',
                title="Risk Stratification",
                color='Risk Group',
                color_discrete_map={
                    'Favorable': '#48BB78',
                    'Intermediate': '#ECC94B',
                    'Adverse': '#F56565'
                }
            )
            fig_risk.update_layout(height=300)
            st.plotly_chart(fig_risk, use_container_width=True)
    
    with viz_tab3:
        # Treatment waterfall
        treatment_data = pd.DataFrame({
            'Treatment': ['Chemotherapy', 'Immunotherapy', 'Targeted Therapy', 
                         'Transplant', 'CAR-T', 'Radiation'],
            'Patients': [
                int(cohort_size * 0.85),
                int(cohort_size * 0.45),
                int(cohort_size * 0.35),
                int(cohort_size * 0.20),
                int(cohort_size * 0.08),
                int(cohort_size * 0.30)
            ]
        })
        treatment_data = treatment_data.sort_values('Patients', ascending=True)
        
        fig_treatment = px.bar(
            treatment_data,
            x='Patients',
            y='Treatment',
            orientation='h',
            title="Treatment Modalities Received",
            color='Patients',
            color_continuous_scale='Purples'
        )
        fig_treatment.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_treatment, use_container_width=True)
    
    with viz_tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            # Response distribution
            response_data = pd.DataFrame({
                'Response': ['CR', 'PR', 'SD', 'PD'],
                'Patients': [
                    int(cohort_size * 0.45),
                    int(cohort_size * 0.25),
                    int(cohort_size * 0.15),
                    int(cohort_size * 0.15)
                ]
            })
            fig_response = px.pie(
                response_data,
                values='Patients',
                names='Response',
                title="Best Response Achieved",
                color='Response',
                color_discrete_map={
                    'CR': '#48BB78',
                    'PR': '#68D391',
                    'SD': '#ECC94B',
                    'PD': '#F56565'
                }
            )
            fig_response.update_layout(height=300)
            st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            # Kaplan-Meier style survival curve (simulated)
            months = list(range(0, 61, 6))
            survival_prob = [1.0, 0.92, 0.85, 0.78, 0.72, 0.68, 0.65, 0.62, 0.60, 0.58, 0.56]
            
            fig_km = go.Figure()
            fig_km.add_trace(go.Scatter(
                x=months,
                y=survival_prob,
                mode='lines',
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)',
                line=dict(color='#667eea', width=2),
                name='OS'
            ))
            fig_km.update_layout(
                title="Overall Survival Estimate",
                xaxis_title="Months",
                yaxis_title="Survival Probability",
                yaxis=dict(range=[0, 1.05]),
                height=300
            )
            st.plotly_chart(fig_km, use_container_width=True)

# Action buttons
st.markdown("---")

col_actions = st.columns([1, 1, 1, 2])

with col_actions[0]:
    if st.button("💾 Save Cohort", type="primary", use_container_width=True):
        st.success("Cohort saved successfully!")

with col_actions[1]:
    if st.button("📤 Export Data", use_container_width=True):
        st.info("Preparing export... Choose format below.")
        export_format = st.selectbox(
            "Export Format",
            options=["CSV", "JSON", "Parquet", "Excel"]
        )

with col_actions[2]:
    if st.button("📊 Generate Report", use_container_width=True):
        st.info("Generating comprehensive cohort report...")

with col_actions[3]:
    st.markdown("""
    <div style="text-align: right; color: #718096; font-size: 0.9rem; padding-top: 0.5rem;">
        💡 Need custom analysis? <a href="#">Contact our research team</a>
    </div>
    """, unsafe_allow_html=True)

# Sample data preview
with st.expander("📋 Sample Data Preview (De-identified)", expanded=False):
    sample_data = pd.DataFrame({
        'Patient ID': [f'PT-{i:04d}' for i in range(1, 11)],
        'Age': [random.randint(35, 75) for _ in range(10)],
        'Sex': [random.choice(['M', 'F']) for _ in range(10)],
        'Stage': [random.choice(['II', 'III', 'IV']) for _ in range(10)],
        'Risk Group': [random.choice(['Favorable', 'Intermediate', 'Adverse']) for _ in range(10)],
        'First Treatment': [random.choice(['R-CHOP', 'VRd', '7+3', 'Venetoclax-Aza']) for _ in range(10)],
        'Best Response': [random.choice(['CR', 'PR', 'SD']) for _ in range(10)],
        'PFS (mo)': [random.randint(6, 48) for _ in range(10)],
        'Status': [random.choice(['Alive', 'Deceased', 'Alive']) for _ in range(10)],
    })
    st.dataframe(sample_data, use_container_width=True)

