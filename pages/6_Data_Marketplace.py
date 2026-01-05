"""
Data Marketplace Page
Browse and license healthcare datasets for research
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import random
from components.navigation import render_navigation

# Page config
st.set_page_config(
    page_title="Data Marketplace - HealthDB",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    .marketplace-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .marketplace-hero::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 50%;
        height: 100%;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.1) 100%);
        pointer-events: none;
    }
    .marketplace-hero h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .product-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 1rem;
        overflow: hidden;
        transition: all 0.3s ease;
        height: 100%;
    }
    .product-card:hover {
        box-shadow: 0 10px 40px rgba(0,0,0,0.12);
        transform: translateY(-4px);
    }
    .product-header {
        padding: 1.25rem;
        border-bottom: 1px solid #f3f4f6;
    }
    .product-body {
        padding: 1.25rem;
    }
    .product-tag {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.25rem;
        margin-bottom: 0.25rem;
    }
    .tag-hematologic { background: #dbeafe; color: #1e40af; }
    .tag-solid { background: #fce7f3; color: #9d174d; }
    .tag-molecular { background: #d1fae5; color: #065f46; }
    .tag-outcomes { background: #fef3c7; color: #92400e; }
    
    .product-stat {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .price-tag {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .featured-badge {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        position: absolute;
        top: 1rem;
        right: 1rem;
    }
    
    .filter-section {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    .tier-card {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .tier-card:hover {
        border-color: #6366f1;
    }
    .tier-card.selected {
        border-color: #6366f1;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    }
    
    .completeness-bar {
        height: 8px;
        border-radius: 4px;
        background: #e5e7eb;
        overflow: hidden;
    }
    .completeness-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
    }
</style>
""", unsafe_allow_html=True)

render_navigation()

# Demo user setup
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
    st.session_state.username = "Demo Researcher"

# Hero section
st.markdown("""
<div class="marketplace-hero">
    <h1>🛒 Data Marketplace</h1>
    <p style="font-size: 1.1rem; opacity: 0.9; max-width: 600px;">
        Access high-quality, de-identified healthcare datasets for your research. 
        Ethically sourced with patient consent and IRB approval.
    </p>
</div>
""", unsafe_allow_html=True)

# Search and filter bar
col_search, col_category, col_sort = st.columns([3, 1, 1])

with col_search:
    search_query = st.text_input(
        "Search datasets",
        placeholder="Search by cancer type, treatment, or keyword...",
        label_visibility="collapsed"
    )

with col_category:
    category_filter = st.selectbox(
        "Category",
        options=["All Categories", "Hematologic Malignancies", "Solid Tumors", "Pan-Cancer"],
        label_visibility="collapsed"
    )

with col_sort:
    sort_by = st.selectbox(
        "Sort by",
        options=["Relevance", "Patients (High to Low)", "Price (Low to High)", "Recently Added"],
        label_visibility="collapsed"
    )

# Filters
with st.expander("🔍 Advanced Filters", expanded=False):
    filter_cols = st.columns(4)
    
    with filter_cols[0]:
        st.markdown("**Data Categories**")
        include_demographics = st.checkbox("Demographics", value=True)
        include_diagnoses = st.checkbox("Diagnoses", value=True)
        include_treatments = st.checkbox("Treatments", value=True)
        include_outcomes = st.checkbox("Outcomes", value=True)
    
    with filter_cols[1]:
        st.markdown("**Molecular Data**")
        include_molecular = st.checkbox("Molecular/Genetic", value=False)
        include_genomics = st.checkbox("Genomics", value=False)
        include_biomarkers = st.checkbox("Biomarkers", value=False)
    
    with filter_cols[2]:
        st.markdown("**Access Level**")
        access_level = st.radio(
            "Access",
            options=["Any", "Aggregate Only", "De-identified", "Limited Dataset"],
            label_visibility="collapsed"
        )
    
    with filter_cols[3]:
        st.markdown("**Patient Count**")
        min_patients = st.number_input("Minimum patients", min_value=0, value=100)
        date_range = st.date_input("Data from after", value=datetime(2015, 1, 1))

st.markdown("---")

# Featured products
st.subheader("⭐ Featured Datasets")

featured_products = [
    {
        "name": "Comprehensive DLBCL Outcomes Registry",
        "description": "Largest de-identified DLBCL dataset with 5-year outcomes, molecular data, and treatment details",
        "cancer_type": "Diffuse Large B-Cell Lymphoma",
        "category": "Hematologic",
        "patients": 4250,
        "records": 125000,
        "data_types": ["Demographics", "Diagnoses", "Treatments", "Outcomes", "Molecular"],
        "completeness": 94,
        "price_academic": 15000,
        "price_commercial": 75000,
        "featured": True
    },
    {
        "name": "AML Treatment Response Database",
        "description": "Acute myeloid leukemia patients with FLT3/NPM1 status, treatment responses, and MRD data",
        "cancer_type": "Acute Myeloid Leukemia",
        "category": "Hematologic",
        "patients": 2800,
        "records": 84000,
        "data_types": ["Demographics", "Diagnoses", "Treatments", "Molecular", "MRD"],
        "completeness": 91,
        "price_academic": 12000,
        "price_commercial": 60000,
        "featured": True
    },
    {
        "name": "CAR-T Real-World Outcomes",
        "description": "Multi-center CAR-T therapy outcomes across lymphoma and leukemia with CRS/ICANS data",
        "cancer_type": "Multiple (B-cell malignancies)",
        "category": "Hematologic",
        "patients": 890,
        "records": 35600,
        "data_types": ["Demographics", "Treatments", "Toxicity", "Response", "Outcomes"],
        "completeness": 97,
        "price_academic": 25000,
        "price_commercial": 125000,
        "featured": True
    }
]

featured_cols = st.columns(3)

for i, product in enumerate(featured_products):
    with featured_cols[i]:
        # Tags
        tags_html = ""
        for dt in product["data_types"][:3]:
            tag_class = "tag-molecular" if "Molecular" in dt else "tag-outcomes" if "Outcome" in dt else "tag-hematologic"
            tags_html += f'<span class="product-tag {tag_class}">{dt}</span>'
        
        st.markdown(f"""
        <div class="product-card" style="position: relative;">
            <span class="featured-badge">⭐ Featured</span>
            <div class="product-header">
                <h4 style="margin: 0 0 0.5rem 0; padding-right: 80px;">{product['name']}</h4>
                <p style="color: #6b7280; font-size: 0.9rem; margin: 0;">{product['description'][:100]}...</p>
            </div>
            <div class="product-body">
                <div style="margin-bottom: 1rem;">{tags_html}</div>
                
                <div class="product-stat">
                    <span>👥</span> {product['patients']:,} patients
                </div>
                <div class="product-stat">
                    <span>📊</span> {product['records']:,} records
                </div>
                <div class="product-stat">
                    <span>🎯</span> {product['cancer_type']}
                </div>
                
                <div style="margin: 1rem 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;">
                        <span>Completeness</span>
                        <span style="font-weight: 600;">{product['completeness']}%</span>
                    </div>
                    <div class="completeness-bar">
                        <div class="completeness-fill" style="width: {product['completeness']}%;"></div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280;">From</div>
                        <div class="price-tag">${product['price_academic']:,}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("View Details", key=f"view_{product['name']}", use_container_width=True):
            st.session_state.selected_product = product

st.markdown("---")

# All Products
st.subheader("📦 All Datasets")

all_products = [
    {
        "name": "Multiple Myeloma Longitudinal Study",
        "cancer_type": "Multiple Myeloma",
        "category": "Hematologic",
        "patients": 3200,
        "completeness": 88,
        "price": 18000,
        "data_types": ["Demographics", "Treatments", "Outcomes"]
    },
    {
        "name": "Follicular Lymphoma Transformation Registry",
        "cancer_type": "Follicular Lymphoma",
        "category": "Hematologic",
        "patients": 1450,
        "completeness": 92,
        "price": 12000,
        "data_types": ["Demographics", "Pathology", "Outcomes"]
    },
    {
        "name": "NSCLC Immunotherapy Response Database",
        "cancer_type": "Non-Small Cell Lung Cancer",
        "category": "Solid Tumor",
        "patients": 5600,
        "completeness": 85,
        "price": 22000,
        "data_types": ["Demographics", "Biomarkers", "Treatments", "Outcomes"]
    },
    {
        "name": "Breast Cancer HER2+ Treatment Outcomes",
        "cancer_type": "Breast Cancer",
        "category": "Solid Tumor",
        "patients": 4100,
        "completeness": 90,
        "price": 20000,
        "data_types": ["Demographics", "Molecular", "Treatments", "Outcomes"]
    },
    {
        "name": "CLL Treatment Era Comparison",
        "cancer_type": "Chronic Lymphocytic Leukemia",
        "category": "Hematologic",
        "patients": 2800,
        "completeness": 87,
        "price": 15000,
        "data_types": ["Demographics", "Cytogenetics", "Treatments"]
    },
    {
        "name": "Pediatric ALL Outcomes Database",
        "cancer_type": "Acute Lymphoblastic Leukemia",
        "category": "Hematologic",
        "patients": 1200,
        "completeness": 95,
        "price": 18000,
        "data_types": ["Demographics", "Molecular", "MRD", "Outcomes"]
    },
]

# Display as grid
product_cols = st.columns(3)

for i, product in enumerate(all_products):
    with product_cols[i % 3]:
        tags_html = ""
        for dt in product["data_types"][:2]:
            tag_class = "tag-solid" if product["category"] == "Solid Tumor" else "tag-hematologic"
            tags_html += f'<span class="product-tag {tag_class}">{dt}</span>'
        
        st.markdown(f"""
        <div class="product-card">
            <div class="product-header">
                <h4 style="margin: 0 0 0.5rem 0;">{product['name']}</h4>
                <span style="color: #6b7280; font-size: 0.85rem;">{product['cancer_type']}</span>
            </div>
            <div class="product-body">
                <div style="margin-bottom: 0.75rem;">{tags_html}</div>
                
                <div class="product-stat">
                    <span>👥</span> {product['patients']:,} patients
                </div>
                
                <div style="margin: 0.75rem 0;">
                    <div class="completeness-bar">
                        <div class="completeness-fill" style="width: {product['completeness']}%;"></div>
                    </div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">{product['completeness']}% complete</div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="price-tag">${product['price']:,}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Details", key=f"details_{product['name']}", use_container_width=True):
            st.info(f"Opening details for {product['name']}...")
        
        st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# Pricing Tiers
st.subheader("💳 Pricing Tiers")

tier_cols = st.columns(4)

tiers = [
    {
        "name": "Academic",
        "discount": "60% off",
        "description": "For universities and non-profit research",
        "features": ["IRB required", "Publication rights", "1-year license", "Email support"],
        "icon": "🎓"
    },
    {
        "name": "Startup",
        "discount": "30% off",
        "description": "For early-stage companies (<50 employees)",
        "features": ["IRB preferred", "Internal use", "1-year license", "Priority support"],
        "icon": "🚀"
    },
    {
        "name": "Enterprise",
        "discount": "Standard",
        "description": "For established companies",
        "features": ["Full commercial rights", "API access", "Multi-year options", "Dedicated support"],
        "icon": "🏢"
    },
    {
        "name": "Pharma",
        "discount": "Premium",
        "description": "For pharmaceutical companies",
        "features": ["Full commercial rights", "Custom extracts", "Unlimited users", "White-glove support"],
        "icon": "💊"
    }
]

for i, tier in enumerate(tiers):
    with tier_cols[i]:
        st.markdown(f"""
        <div class="tier-card">
            <div style="font-size: 2rem;">{tier['icon']}</div>
            <h4 style="margin: 0.5rem 0;">{tier['name']}</h4>
            <div style="color: #6366f1; font-weight: 600; margin-bottom: 0.5rem;">{tier['discount']}</div>
            <p style="color: #6b7280; font-size: 0.85rem; min-height: 40px;">{tier['description']}</p>
            <ul style="text-align: left; color: #4b5563; font-size: 0.85rem; padding-left: 1.25rem; margin-top: 1rem;">
                {''.join([f'<li>{f}</li>' for f in tier['features']])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Custom Data Request
st.subheader("🎯 Need Custom Data?")

col_custom, col_form = st.columns([1, 1])

with col_custom:
    st.markdown("""
    Can't find what you're looking for? We can create custom data extracts tailored to your research needs:
    
    - **Custom cohort definitions** - Specific patient populations
    - **Additional data fields** - Variables not in standard datasets  
    - **Longitudinal panels** - Track patients over specific timeframes
    - **Linked datasets** - Combine multiple data sources
    - **API access** - Real-time data queries
    
    Our data team will work with you to understand your needs and provide a custom quote.
    """)

with col_form:
    with st.form("custom_request"):
        st.text_input("Your Name")
        st.text_input("Organization")
        st.text_input("Email")
        st.text_area("Describe your data needs", height=100)
        
        submitted = st.form_submit_button("Submit Request", use_container_width=True)
        
        if submitted:
            st.success("Thank you! Our team will contact you within 24 hours.")

# Footer
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0; margin-top: 2rem;">
    <p style="font-size: 0.9rem;">
        All data is ethically sourced with patient consent. 
        IRB approval documentation is provided with each dataset.
    </p>
    <p style="font-size: 0.85rem;">
        Questions? Contact <a href="mailto:data@healthdb.ai">data@healthdb.ai</a>
    </p>
</div>
""", unsafe_allow_html=True)

