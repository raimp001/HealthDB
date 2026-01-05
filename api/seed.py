"""
HealthDB Database Seeder
Populate database with initial data products and sample institutional data
"""
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Institution, DataProduct


def seed_institutions(db: Session) -> None:
    """Seed partner institutions"""
    institutions = [
        {
            "name": "Stanford Cancer Center",
            "type": "Academic Medical Center",
            "city": "Stanford",
            "state": "California",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "Mayo Clinic",
            "type": "Academic Medical Center",
            "city": "Rochester",
            "state": "Minnesota",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "MD Anderson Cancer Center",
            "type": "Cancer Center",
            "city": "Houston",
            "state": "Texas",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "Memorial Sloan Kettering",
            "type": "Cancer Center",
            "city": "New York",
            "state": "New York",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "Dana-Farber Cancer Institute",
            "type": "Cancer Center",
            "city": "Boston",
            "state": "Massachusetts",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "Fred Hutchinson Cancer Center",
            "type": "Cancer Center",
            "city": "Seattle",
            "state": "Washington",
            "country": "USA",
            "emr_system": "Cerner",
        },
        {
            "name": "Cleveland Clinic",
            "type": "Academic Medical Center",
            "city": "Cleveland",
            "state": "Ohio",
            "country": "USA",
            "emr_system": "Epic",
        },
        {
            "name": "Johns Hopkins Hospital",
            "type": "Academic Medical Center",
            "city": "Baltimore",
            "state": "Maryland",
            "country": "USA",
            "emr_system": "Epic",
        },
    ]

    for inst_data in institutions:
        existing = db.query(Institution).filter(
            Institution.name == inst_data["name"]
        ).first()
        if not existing:
            institution = Institution(**inst_data)
            db.add(institution)

    db.commit()


def seed_data_products(db: Session) -> None:
    """Seed data products for the marketplace"""
    products = [
        {
            "name": "Comprehensive DLBCL Outcomes Registry",
            "description": "Largest de-identified DLBCL dataset with 5-year outcomes, molecular data, and treatment details including CAR-T and novel therapies. Includes IPI scores, cell of origin classification, and MRD data.",
            "category": "Hematologic",
            "cancer_types": ["Diffuse Large B-Cell Lymphoma"],
            "data_categories": ["Demographics", "Diagnoses", "Treatments", "Outcomes", "Molecular", "MRD"],
            "patient_count": 0,  # Will be updated from actual data
            "record_count": 0,
            "completeness_score": 94.0,
            "date_range_start": date(2015, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 15000,
                "startup": 35000,
                "enterprise": 75000,
                "pharma": 150000
            },
            "is_featured": True,
        },
        {
            "name": "AML Treatment Response Database",
            "description": "Acute myeloid leukemia patients with FLT3/NPM1 status, treatment responses, and MRD data from multiple centers. Includes cytogenetic risk stratification and transplant outcomes.",
            "category": "Hematologic",
            "cancer_types": ["Acute Myeloid Leukemia"],
            "data_categories": ["Demographics", "Diagnoses", "Treatments", "Molecular", "MRD", "Cytogenetics"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 91.0,
            "date_range_start": date(2016, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 12000,
                "startup": 28000,
                "enterprise": 60000,
                "pharma": 120000
            },
            "is_featured": True,
        },
        {
            "name": "CAR-T Real-World Outcomes",
            "description": "Multi-center CAR-T therapy outcomes across lymphoma and leukemia with CRS/ICANS data and long-term follow-up. Includes bridging therapy, lymphodepletion regimens, and manufacturing data.",
            "category": "Cell Therapy",
            "cancer_types": ["DLBCL", "ALL", "MCL", "Follicular Lymphoma"],
            "data_categories": ["Demographics", "Treatments", "Toxicity", "Response", "Outcomes", "Manufacturing"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 97.0,
            "date_range_start": date(2018, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 25000,
                "startup": 55000,
                "enterprise": 125000,
                "pharma": 250000
            },
            "is_featured": True,
        },
        {
            "name": "Multiple Myeloma Longitudinal Study",
            "description": "Comprehensive myeloma dataset with treatment sequences across multiple lines, response depths (including MRD), and cytogenetic risk factors. Includes transplant and CAR-T outcomes.",
            "category": "Hematologic",
            "cancer_types": ["Multiple Myeloma"],
            "data_categories": ["Demographics", "Treatments", "Cytogenetics", "Outcomes", "MRD"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 88.0,
            "date_range_start": date(2014, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 18000,
                "startup": 40000,
                "enterprise": 85000,
                "pharma": 170000
            },
            "is_featured": False,
        },
        {
            "name": "NSCLC Immunotherapy Response Database",
            "description": "Non-small cell lung cancer patients treated with checkpoint inhibitors, with PD-L1 status, TMB data, and outcomes. Includes combination therapy regimens and biomarker correlations.",
            "category": "Solid Tumor",
            "cancer_types": ["Non-Small Cell Lung Cancer"],
            "data_categories": ["Demographics", "Biomarkers", "Treatments", "Imaging", "Outcomes", "Molecular"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 85.0,
            "date_range_start": date(2016, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 22000,
                "startup": 48000,
                "enterprise": 100000,
                "pharma": 200000
            },
            "is_featured": False,
        },
        {
            "name": "Triple-Negative Breast Cancer Registry",
            "description": "TNBC patients with genomic profiling, treatment histories including neoadjuvant/adjuvant therapy, and long-term recurrence data. Includes BRCA status and immunotherapy outcomes.",
            "category": "Solid Tumor",
            "cancer_types": ["Breast Cancer"],
            "data_categories": ["Demographics", "Pathology", "Genomics", "Treatments", "Outcomes"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 89.0,
            "date_range_start": date(2015, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 16000,
                "startup": 36000,
                "enterprise": 75000,
                "pharma": 150000
            },
            "is_featured": False,
        },
        {
            "name": "CLL Watch & Wait to Treatment Study",
            "description": "Chronic lymphocytic leukemia patients from initial diagnosis through multiple lines of therapy. Includes IGHV status, TP53/del17p, and novel agent outcomes.",
            "category": "Hematologic",
            "cancer_types": ["Chronic Lymphocytic Leukemia"],
            "data_categories": ["Demographics", "Diagnoses", "Molecular", "Treatments", "Outcomes"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 86.0,
            "date_range_start": date(2014, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 14000,
                "startup": 32000,
                "enterprise": 68000,
                "pharma": 135000
            },
            "is_featured": False,
        },
        {
            "name": "Stem Cell Transplant Outcomes Database",
            "description": "Autologous and allogeneic transplant outcomes across hematologic malignancies. Includes conditioning regimens, GVHD data, and long-term survival.",
            "category": "Cell Therapy",
            "cancer_types": ["AML", "ALL", "Lymphoma", "Multiple Myeloma", "MDS"],
            "data_categories": ["Demographics", "Conditioning", "GVHD", "Infections", "Outcomes"],
            "patient_count": 0,
            "record_count": 0,
            "completeness_score": 92.0,
            "date_range_start": date(2010, 1, 1),
            "date_range_end": date.today(),
            "pricing_tiers": {
                "academic": 20000,
                "startup": 45000,
                "enterprise": 95000,
                "pharma": 190000
            },
            "is_featured": False,
        },
    ]

    for product_data in products:
        existing = db.query(DataProduct).filter(
            DataProduct.name == product_data["name"]
        ).first()
        if not existing:
            product = DataProduct(**product_data)
            db.add(product)

    db.commit()


def run_seed():
    """Run all seeders"""
    db = SessionLocal()
    try:
        print("Seeding institutions...")
        seed_institutions(db)
        print("Seeding data products...")
        seed_data_products(db)
        print("Seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

