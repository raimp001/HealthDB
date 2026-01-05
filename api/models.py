"""
HealthDB SQLAlchemy Models
Database models for all platform entities
Compatible with both PostgreSQL and SQLite
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, Numeric, Enum as SQLEnum, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from .database import Base

# Use String for UUID compatibility with SQLite
def generate_uuid():
    return str(uuid.uuid4())


# ============== Enums ==============

class UserType(str, enum.Enum):
    RESEARCHER = "researcher"
    PATIENT = "patient"
    ADMIN = "admin"
    INSTITUTION = "institution"


class ConsentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class TreatmentType(str, enum.Enum):
    CHEMOTHERAPY = "chemotherapy"
    IMMUNOTHERAPY = "immunotherapy"
    TARGETED_THERAPY = "targeted_therapy"
    CAR_T = "car_t"
    STEM_CELL_TRANSPLANT = "stem_cell_transplant"
    RADIATION = "radiation"
    SURGERY = "surgery"
    OTHER = "other"


class ResponseType(str, enum.Enum):
    COMPLETE_RESPONSE = "CR"
    PARTIAL_RESPONSE = "PR"
    STABLE_DISEASE = "SD"
    PROGRESSIVE_DISEASE = "PD"
    NOT_EVALUATED = "NE"


# ============== User Models ==============

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, default="researcher")
    organization = Column(String(255))
    institution_id = Column(String(36), ForeignKey("institutions.id"))
    role = Column(String(50), default="user")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    institution = relationship("Institution", back_populates="users")
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    cohorts = relationship("ResearchCohort", back_populates="user")
    data_access_logs = relationship("DataAccessLog", back_populates="user")


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    emr_system = Column(String(100))
    fhir_endpoint = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="institution")
    diagnoses = relationship("CancerDiagnosis", back_populates="institution")


# ============== Patient Portal Models ==============

class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True)
    hashed_mrn = Column(String(255), unique=True, index=True)
    points_balance = Column(Integer, default=0)
    total_points_earned = Column(Integer, default=0)
    engagement_level = Column(String(50), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    consents = relationship("Consent", back_populates="patient")
    rewards = relationship("RewardsTransaction", back_populates="patient")
    data_access_logs = relationship("DataAccessLog", back_populates="patient")


class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    consent_type = Column(String(100), nullable=False)
    consent_version = Column(String(50))
    status = Column(String(50), default="pending")
    consent_options = Column(JSON)
    signed_date = Column(DateTime)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    signature = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("PatientProfile", back_populates="consents")


class RewardsTransaction(Base):
    __tablename__ = "rewards_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # earn, redeem
    points = Column(Integer, nullable=False)
    description = Column(Text)
    reference_type = Column(String(100))
    reference_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("PatientProfile", back_populates="rewards")


# ============== Clinical Data Models ==============

class CancerDiagnosis(Base):
    __tablename__ = "cancer_diagnoses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    hashed_patient_id = Column(String(255), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"))
    cancer_type = Column(String(255), nullable=False, index=True)
    icd10_code = Column(String(20))
    diagnosis_date = Column(Date)
    stage = Column(String(50))
    substage = Column(String(50))
    grade = Column(String(50))
    histology = Column(String(255))
    primary_site = Column(String(255))
    laterality = Column(String(50))
    risk_group = Column(String(100))
    performance_status = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="diagnoses")
    treatments = relationship("Treatment", back_populates="diagnosis")
    molecular_data = relationship("MolecularData", back_populates="diagnosis")
    outcomes = relationship("Outcome", back_populates="diagnosis")


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    diagnosis_id = Column(String(36), ForeignKey("cancer_diagnoses.id"), nullable=False)
    treatment_type = Column(String(50), nullable=False)
    regimen_name = Column(String(255))
    line_of_therapy = Column(Integer, default=1)
    start_date = Column(Date)
    end_date = Column(Date)
    cycles_planned = Column(Integer)
    cycles_completed = Column(Integer)
    dose_modifications = Column(JSON)
    intent = Column(String(100))  # curative, palliative, adjuvant, neoadjuvant
    status = Column(String(50))  # ongoing, completed, discontinued
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    diagnosis = relationship("CancerDiagnosis", back_populates="treatments")
    responses = relationship("TreatmentResponse", back_populates="treatment")


class TreatmentResponse(Base):
    __tablename__ = "treatment_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    treatment_id = Column(String(36), ForeignKey("treatments.id"), nullable=False)
    assessment_date = Column(Date)
    response_criteria = Column(String(100))  # RECIST, Lugano, IMWG
    response_type = Column(String(20))
    mrd_status = Column(String(50))
    mrd_method = Column(String(100))
    imaging_result = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    treatment = relationship("Treatment", back_populates="responses")


class MolecularData(Base):
    __tablename__ = "molecular_data"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    diagnosis_id = Column(String(36), ForeignKey("cancer_diagnoses.id"), nullable=False)
    test_type = Column(String(100))  # NGS, FISH, IHC, Flow Cytometry
    test_date = Column(Date)
    gene = Column(String(100), index=True)
    mutation = Column(String(255))
    variant_allele_frequency = Column(Float)
    interpretation = Column(String(100))
    clinical_significance = Column(String(100))
    raw_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    diagnosis = relationship("CancerDiagnosis", back_populates="molecular_data")


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    diagnosis_id = Column(String(36), ForeignKey("cancer_diagnoses.id"), nullable=False)
    outcome_type = Column(String(100))  # relapse, progression, death, last_follow_up
    outcome_date = Column(Date)
    status = Column(String(100))
    cause = Column(String(255))
    survival_months = Column(Float)
    pfs_months = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    diagnosis = relationship("CancerDiagnosis", back_populates="outcomes")


# ============== Data Marketplace Models ==============

class DataProduct(Base):
    __tablename__ = "data_products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    cancer_types = Column(JSON)
    data_categories = Column(JSON)
    patient_count = Column(Integer)
    record_count = Column(Integer)
    completeness_score = Column(Float)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    pricing_tiers = Column(JSON)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    purchases = relationship("DataPurchase", back_populates="product")


class DataPurchase(Base):
    __tablename__ = "data_purchases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("data_products.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tier = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, approved, rejected, completed
    license_start = Column(Date)
    license_end = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("DataProduct", back_populates="purchases")


class DataAccessLog(Base):
    __tablename__ = "data_access_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    patient_id = Column(String(36), ForeignKey("patient_profiles.id"))
    product_id = Column(String(36), ForeignKey("data_products.id"))
    access_type = Column(String(100))
    data_type = Column(String(100))
    purpose = Column(Text)
    query_hash = Column(String(255))
    record_count = Column(Integer)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="data_access_logs")
    patient = relationship("PatientProfile", back_populates="data_access_logs")


# ============== Research Models ==============

class ResearchCohort(Base):
    __tablename__ = "research_cohorts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    criteria = Column(JSON)
    patient_count = Column(Integer)
    is_saved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cohorts")

