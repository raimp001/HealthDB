"""
HealthDB API - FastAPI Backend
Main application entry point with real database integration
"""
from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
import uuid
import os
from jose import jwt
import hashlib

from sqlalchemy.orm import Session

from sqlalchemy import text
from .database import get_db, init_db, engine
from .models import (
    Base, User, PatientProfile, Consent, ConsentTemplate,
    CancerDiagnosis, Treatment, DataProduct, DataAccessLog, ResearchCohort,
    MedicalRecordConnection, ExtractedMedicalData, RewardsTransaction,
    Study, RegulatorySubmission, ExtractionJob, EMRConnection, Institution,
    StudyCollaborator, StudyDocument, StudyComment, DiseaseVariableSet
)
from .repositories import (
    UserRepository, PatientRepository, ClinicalDataRepository,
    CohortRepository, DataProductRepository, DataAccessLogRepository
)

# Initialize FastAPI app
app = FastAPI(
    title="HealthDB API",
    description="Longitudinal Healthcare Database Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.healthdb.ai",
        "https://healthdb.ai",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


# ============== Startup Events ==============

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Clean up any placeholder/mock data products (no real patient data)
    db = next(get_db())
    try:
        # Remove data products with 0 patients (placeholder data)
        deleted = db.query(DataProduct).filter(DataProduct.patient_count == 0).delete()
        if deleted > 0:
            print(f"Removed {deleted} placeholder data products")
            db.commit()
    except Exception as e:
        print(f"Cleanup note: {e}")
        db.rollback()
    finally:
        db.close()


# ============== Pydantic Models ==============

class UserBase(BaseModel):
    email: EmailStr
    name: str
    organization: Optional[str] = None

class UserCreate(UserBase):
    password: str
    user_type: str = "researcher"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    organization: Optional[str]
    user_type: str
    created_at: datetime
    is_verified: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PatientProfileResponse(BaseModel):
    id: str
    points_balance: int
    total_points_earned: int
    engagement_level: str
    consents_active: int
    studies_contributing: int
    data_accesses: int

class ConsentRequest(BaseModel):
    consent_type: str
    consent_options: Dict[str, bool]
    signature: str

class ConsentResponse(BaseModel):
    id: str
    consent_type: str
    status: str
    signed_date: Optional[datetime]
    expires_at: Optional[datetime]

class RewardResponse(BaseModel):
    date: str
    activity: str
    points: int

class DataProductSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    cancer_types: List[str]
    patient_count: int
    completeness_score: float
    price_from: float
    is_featured: bool

class DataProductDetail(DataProductSummary):
    data_categories: List[str]
    record_count: int
    date_range_start: Optional[date]
    date_range_end: Optional[date]
    pricing_tiers: Dict[str, float]
    category: Optional[str]

class CohortCriteria(BaseModel):
    cancer_types: Optional[List[str]] = None
    stages: Optional[List[str]] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    molecular_markers: Optional[List[str]] = None
    treatment_types: Optional[List[str]] = None
    min_follow_up_months: Optional[int] = None

class CohortResult(BaseModel):
    cohort_id: Optional[str] = None
    patient_count: int
    data_points: int
    diagnosis_count: int
    treatment_count: int
    molecular_count: int

class SaveCohortRequest(BaseModel):
    name: str
    description: Optional[str] = None
    criteria: CohortCriteria

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    organization: str
    message: str
    interest_type: str


# ============== Study & Regulatory Models ==============

class CreateStudyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    cohort_id: Optional[str] = None
    principal_investigator: Optional[str] = None
    selected_variables: Optional[List[str]] = None

class StudyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    patient_count: Optional[int]
    created_at: datetime
    regulatory_status: Dict[str, str]

class RegulatorySubmissionResponse(BaseModel):
    id: str
    document_type: str
    status: str
    protocol_number: Optional[str]
    institution_name: Optional[str]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    expires_at: Optional[datetime]

class CreateRegulatoryRequest(BaseModel):
    study_id: str
    document_type: str  # irb_protocol, dua, reliance_agreement
    institution_id: Optional[str] = None

class ExtractionJobRequest(BaseModel):
    study_id: str
    variables: List[str]
    output_format: str = "csv"
    deidentification_level: str = "limited_dataset"

class ExtractionJobResponse(BaseModel):
    id: str
    job_name: str
    status: str
    patient_count: Optional[int]
    variable_count: Optional[int]
    output_format: str
    estimated_completion: Optional[datetime]
    download_url: Optional[str]
    created_at: datetime

class EMRConnectionResponse(BaseModel):
    id: str
    institution_name: str
    emr_vendor: str
    status: str
    last_sync: Optional[datetime]
    patient_count: int
    data_completeness_score: float


# ============== Consent & Medical Records Models ==============

class ConsentTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    consent_type: str
    version: str
    content: str
    data_categories: List[str]
    duration_months: Optional[int]

class SignConsentRequest(BaseModel):
    template_id: str
    signature: str  # Base64 encoded signature or typed name
    consent_options: Dict[str, bool]  # Granular consent choices

class MedicalConnectionRequest(BaseModel):
    source_type: str  # epic_mychart, cerner, manual_upload
    source_name: str  # Hospital/provider name
    access_code: Optional[str] = None  # OAuth code or auth token

class MedicalConnectionResponse(BaseModel):
    id: str
    source_type: str
    source_name: str
    connection_status: str
    last_sync: Optional[datetime]
    records_synced: int
    created_at: datetime

class ExtractedDataResponse(BaseModel):
    id: str
    data_category: str
    data_type: Optional[str]
    extracted_date: datetime
    original_date: Optional[date]
    data_quality_score: Optional[float]
    summary: Dict[str, Any]  # De-identified summary for patient view

class PatientDataSummary(BaseModel):
    total_records: int
    categories: Dict[str, int]
    last_sync: Optional[datetime]
    completeness_score: float
    connections: List[MedicalConnectionResponse]


# ============== Helper Functions ==============

def create_token(user_id: str, user_type: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": str(user_id),
        "type": user_type,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Verify JWT token"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Require authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    return verify_token(credentials)


def hash_password(password: str) -> str:
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============== Auth Endpoints ==============

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (patient or researcher)"""
    user_repo = UserRepository(db)

    # Check if email exists
    existing = user_repo.get_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user_type = "patient" if user.user_type == "patient" else "researcher"
    new_user = user_repo.create(
        email=user.email,
        password_hash=hash_password(user.password),
        name=user.name,
        user_type=user_type,
        organization=user.organization,
    )

    # Create patient profile if patient
    if user_type == "patient":
        patient_repo = PatientRepository(db)
        patient_repo.create_profile(new_user.id)

    token = create_token(str(new_user.id), user.user_type)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            name=new_user.name,
            organization=new_user.organization,
            user_type=user.user_type,
            created_at=new_user.created_at,
            is_verified=new_user.is_verified,
        )
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(credentials.email)

    if not user or user.password_hash != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login
    user_repo.update_last_login(user.id)

    token = create_token(str(user.id), user.user_type)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            organization=user.organization,
            user_type=user.user_type,
            created_at=user.created_at,
            is_verified=user.is_verified,
        )
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(UUID(token_data["sub"]))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        organization=user.organization,
        user_type=user.user_type,
        created_at=user.created_at,
        is_verified=user.is_verified,
    )


# ============== Patient Portal Endpoints ==============

@app.get("/api/patient/profile", response_model=PatientProfileResponse)
async def get_patient_profile(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient portal profile"""
    if token_data.get("type") != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")

    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))

    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Get counts
    consents = patient_repo.get_consents(profile.id)
    active_consents = len([c for c in consents if c.status == "active"])
    studies_count = patient_repo.get_studies_count(profile.id)
    access_logs = patient_repo.get_data_access_log(profile.id)

    return PatientProfileResponse(
        id=str(profile.id),
        points_balance=profile.points_balance,
        total_points_earned=profile.total_points_earned,
        engagement_level=profile.engagement_level,
        consents_active=active_consents,
        studies_contributing=studies_count,
        data_accesses=len(access_logs),
    )


@app.get("/api/patient/consents", response_model=List[ConsentResponse])
async def get_patient_consents(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient's consents"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))

    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    consents = patient_repo.get_consents(profile.id)

    return [
        ConsentResponse(
            id=str(c.id),
            consent_type=c.consent_type,
            status=c.status.value,
            signed_date=c.signed_date,
            expires_at=c.expires_at,
        )
        for c in consents
    ]


@app.post("/api/patient/consents", response_model=ConsentResponse)
async def sign_consent(
    consent: ConsentRequest,
    request: Request,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Sign a new consent"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))

    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    new_consent = patient_repo.create_consent(
        patient_id=profile.id,
        consent_type=consent.consent_type,
        consent_options=consent.consent_options,
        signature=consent.signature,
        ip_address=get_client_ip(request),
    )

    return ConsentResponse(
        id=str(new_consent.id),
        consent_type=new_consent.consent_type,
        status=new_consent.status.value,
        signed_date=new_consent.signed_date,
        expires_at=new_consent.expires_at,
    )


@app.get("/api/patient/rewards")
async def get_patient_rewards(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient rewards history"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))

    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    rewards = patient_repo.get_rewards_history(profile.id)

    return {
        "total_earned": profile.total_points_earned,
        "total_redeemed": profile.total_points_earned - profile.points_balance,
        "available_balance": profile.points_balance,
        "cash_value": profile.points_balance / 100,  # 100 points = $1
        "history": [
            {
                "date": r.created_at.strftime("%Y-%m-%d"),
                "activity": r.description,
                "points": r.points,
            }
            for r in rewards
        ]
    }


@app.get("/api/patient/data-access-log")
async def get_data_access_log(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get log of who accessed patient's data"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))

    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    logs = patient_repo.get_data_access_log(profile.id)

    return [
        {
            "date": log.created_at.strftime("%Y-%m-%d"),
            "institution": "Research Institution",  # Would join with user/institution
            "data_type": log.data_type,
            "purpose": log.purpose,
        }
        for log in logs
    ]


# ============== Enhanced Consent Endpoints ==============

@app.get("/api/consent/templates", response_model=List[ConsentTemplateResponse])
async def get_consent_templates(
    db: Session = Depends(get_db)
):
    """Get available consent templates"""
    templates = db.query(ConsentTemplate).filter(ConsentTemplate.is_active == True).all()
    
    # If no templates exist, create default ones
    if not templates:
        default_templates = [
            {
                "name": "Research Data Sharing",
                "description": "Allow your de-identified health data to be used for cancer research",
                "consent_type": "research_data_sharing",
                "version": "1.0",
                "content": """
# Research Data Sharing Consent

By signing this consent, you agree to share your de-identified health information with qualified researchers for the purpose of advancing cancer research.

## What data will be shared?
- Diagnosis information (cancer type, stage, date)
- Treatment history (medications, procedures, outcomes)
- Lab results and biomarkers
- Demographic information (age range, not exact date of birth)

## What will NOT be shared?
- Your name or contact information
- Social Security Number
- Exact dates (only month/year)
- Any information that could directly identify you

## Your Rights
- You can revoke this consent at any time
- You can request a list of who accessed your data
- You earn rewards for contributing to research

## Duration
This consent is valid for 24 months from signing date.
                """,
                "data_categories": ["demographics", "diagnosis", "treatment", "lab_results", "outcomes"],
                "duration_months": 24,
            },
            {
                "name": "Clinical Trial Matching",
                "description": "Allow researchers to contact you about relevant clinical trials",
                "consent_type": "clinical_trial_matching",
                "version": "1.0",
                "content": """
# Clinical Trial Matching Consent

By signing this consent, you allow HealthDB to match your profile against available clinical trials and notify you of potential opportunities.

## What this means
- Your medical profile will be compared against trial eligibility criteria
- You will receive notifications about matching trials
- Researchers may request to contact you through our platform

## Your Control
- You choose whether to respond to any trial invitation
- You can opt out at any time
- Your identity is protected until you choose to reveal it

## Duration
This consent is valid for 12 months from signing date.
                """,
                "data_categories": ["demographics", "diagnosis", "treatment"],
                "duration_months": 12,
            },
            {
                "name": "AI/ML Training Data",
                "description": "Allow your anonymized data to be used for training AI models",
                "consent_type": "ai_ml_training",
                "version": "1.0",
                "content": """
# AI/ML Training Data Consent

By signing this consent, you agree to allow your fully anonymized health data to be used for training artificial intelligence and machine learning models.

## Purpose
These AI models are designed to:
- Predict treatment outcomes
- Identify patterns in cancer progression
- Assist doctors in making treatment decisions

## Data Protection
- Data is fully anonymized before use
- No individual patient can be re-identified
- Models are validated for fairness and bias

## Duration
This consent is valid for 36 months from signing date.
                """,
                "data_categories": ["demographics", "diagnosis", "treatment", "molecular", "outcomes"],
                "duration_months": 36,
            },
        ]
        
        for t in default_templates:
            template = ConsentTemplate(**t)
            db.add(template)
        db.commit()
        
        templates = db.query(ConsentTemplate).filter(ConsentTemplate.is_active == True).all()
    
    return [
        ConsentTemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            consent_type=t.consent_type,
            version=t.version,
            content=t.content,
            data_categories=t.data_categories or [],
            duration_months=t.duration_months,
        )
        for t in templates
    ]


@app.post("/api/consent/sign")
async def sign_consent_template(
    request: Request,
    consent_req: SignConsentRequest,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Sign a consent from a template"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Get the template
    template = db.query(ConsentTemplate).filter(ConsentTemplate.id == consent_req.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Consent template not found")
    
    # Check if already has active consent of this type
    existing = db.query(Consent).filter(
        Consent.patient_id == profile.id,
        Consent.consent_type == template.consent_type,
        Consent.status == "active"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active consent of this type")
    
    # Calculate expiration
    expires_at = None
    if template.duration_months:
        expires_at = datetime.utcnow() + timedelta(days=template.duration_months * 30)
    
    # Create the consent
    new_consent = Consent(
        patient_id=profile.id,
        consent_type=template.consent_type,
        consent_version=template.version,
        status="active",
        consent_options=consent_req.consent_options,
        signed_date=datetime.utcnow(),
        expires_at=expires_at,
        signature=consent_req.signature,
        ip_address=get_client_ip(request),
    )
    db.add(new_consent)
    
    # Award points for signing consent
    points_earned = 50  # Base points for consent
    reward = RewardsTransaction(
        patient_id=profile.id,
        transaction_type="earn",
        points=points_earned,
        description=f"Signed {template.name} consent",
        reference_type="consent",
        reference_id=str(new_consent.id),
    )
    db.add(reward)
    
    # Update patient points
    profile.points_balance += points_earned
    profile.total_points_earned += points_earned
    
    db.commit()
    
    return {
        "success": True,
        "consent_id": str(new_consent.id),
        "consent_type": new_consent.consent_type,
        "status": new_consent.status,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "points_earned": points_earned,
        "message": f"Consent signed successfully! You earned {points_earned} points.",
    }


@app.post("/api/consent/{consent_id}/revoke")
async def revoke_consent(
    consent_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Revoke an active consent"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    consent = db.query(Consent).filter(
        Consent.id == consent_id,
        Consent.patient_id == profile.id
    ).first()
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    if consent.status != "active":
        raise HTTPException(status_code=400, detail="Consent is not active")
    
    consent.status = "revoked"
    consent.revoked_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Consent has been revoked. Your data will no longer be shared under this consent.",
    }


# ============== Medical Records Connection Endpoints ==============

@app.get("/api/patient/connections", response_model=List[MedicalConnectionResponse])
async def get_medical_connections(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient's medical record connections"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    connections = db.query(MedicalRecordConnection).filter(
        MedicalRecordConnection.patient_id == profile.id
    ).all()
    
    return [
        MedicalConnectionResponse(
            id=str(c.id),
            source_type=c.source_type,
            source_name=c.source_name,
            connection_status=c.connection_status,
            last_sync=c.last_sync,
            records_synced=c.records_synced,
            created_at=c.created_at,
        )
        for c in connections
    ]


@app.post("/api/patient/connections")
async def connect_medical_records(
    connection_req: MedicalConnectionRequest,
    background_tasks: BackgroundTasks,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Connect to a medical records source"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Check for active consent
    active_consent = db.query(Consent).filter(
        Consent.patient_id == profile.id,
        Consent.consent_type == "research_data_sharing",
        Consent.status == "active"
    ).first()
    
    if not active_consent:
        raise HTTPException(
            status_code=400, 
            detail="You must sign the Research Data Sharing consent before connecting medical records"
        )
    
    # Create connection record
    connection = MedicalRecordConnection(
        patient_id=profile.id,
        source_type=connection_req.source_type,
        source_name=connection_req.source_name,
        connection_status="pending",
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    # Simulate async data extraction (in production, this would be a real EMR integration)
    background_tasks.add_task(
        simulate_data_extraction,
        connection_id=str(connection.id),
        patient_id=str(profile.id),
    )
    
    return {
        "success": True,
        "connection_id": str(connection.id),
        "status": "pending",
        "message": "Connection initiated. Data extraction will begin shortly.",
    }


async def simulate_data_extraction(connection_id: str, patient_id: str):
    """Simulate extracting de-identified data from medical records"""
    import asyncio
    import random
    
    # Simulate processing time
    await asyncio.sleep(2)
    
    # Get fresh database session
    from .database import SessionLocal
    db = SessionLocal()
    
    try:
        connection = db.query(MedicalRecordConnection).filter(
            MedicalRecordConnection.id == connection_id
        ).first()
        
        if not connection:
            return
        
        # Update connection status
        connection.connection_status = "connected"
        connection.last_sync = datetime.utcnow()
        
        # Generate simulated de-identified data categories
        data_categories = [
            ("demographics", "age_range", {"age_range": "45-54", "sex": "M", "race": "White"}),
            ("diagnosis", "cancer_diagnosis", {
                "cancer_type": random.choice(["DLBCL", "AML", "Breast Cancer", "NSCLC"]),
                "stage": random.choice(["Stage II", "Stage III", "Stage IV"]),
                "diagnosis_year": random.randint(2018, 2024),
                "icd10": random.choice(["C83.3", "C92.0", "C50.9", "C34.9"]),
            }),
            ("treatment", "chemotherapy", {
                "regimen": random.choice(["R-CHOP", "7+3", "AC-T", "Pembrolizumab"]),
                "cycles": random.randint(4, 8),
                "start_year": random.randint(2019, 2024),
                "status": random.choice(["completed", "ongoing"]),
            }),
            ("lab_results", "blood_counts", {
                "wbc_range": "4.5-11.0",
                "hemoglobin_range": "12-16",
                "platelet_range": "150-400",
                "test_count": random.randint(10, 50),
            }),
            ("molecular", "genomic_testing", {
                "test_type": random.choice(["NGS", "FISH", "IHC"]),
                "genes_tested": random.randint(50, 500),
                "mutations_found": random.randint(0, 5),
                "has_actionable": random.choice([True, False]),
            }),
        ]
        
        records_count = 0
        for category, data_type, data in data_categories:
            extracted = ExtractedMedicalData(
                connection_id=connection_id,
                patient_id=patient_id,
                data_category=category,
                data_type=data_type,
                original_date=date.today() - timedelta(days=random.randint(30, 365)),
                deidentified_data=data,
                data_quality_score=random.uniform(75, 98),
                is_verified=True,
                verification_date=datetime.utcnow(),
            )
            db.add(extracted)
            records_count += 1
        
        connection.records_synced = records_count
        
        # Award points for connecting records
        profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if profile:
            points_earned = 100  # Points for connecting records
            reward = RewardsTransaction(
                patient_id=patient_id,
                transaction_type="earn",
                points=points_earned,
                description=f"Connected medical records from {connection.source_name}",
                reference_type="connection",
                reference_id=connection_id,
            )
            db.add(reward)
            profile.points_balance += points_earned
            profile.total_points_earned += points_earned
        
        db.commit()
        
    except Exception as e:
        print(f"Error in data extraction: {e}")
        if connection:
            connection.connection_status = "error"
            connection.error_message = str(e)
            db.commit()
    finally:
        db.close()


@app.get("/api/patient/extracted-data", response_model=List[ExtractedDataResponse])
async def get_extracted_data(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient's extracted de-identified data"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    extracted = db.query(ExtractedMedicalData).filter(
        ExtractedMedicalData.patient_id == profile.id
    ).order_by(ExtractedMedicalData.extracted_date.desc()).all()
    
    return [
        ExtractedDataResponse(
            id=str(e.id),
            data_category=e.data_category,
            data_type=e.data_type,
            extracted_date=e.extracted_date,
            original_date=e.original_date,
            data_quality_score=e.data_quality_score,
            summary=e.deidentified_data or {},
        )
        for e in extracted
    ]


@app.get("/api/patient/data-summary", response_model=PatientDataSummary)
async def get_patient_data_summary(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get summary of patient's contributed data"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Get connections
    connections = db.query(MedicalRecordConnection).filter(
        MedicalRecordConnection.patient_id == profile.id
    ).all()
    
    # Get extracted data counts by category
    extracted = db.query(ExtractedMedicalData).filter(
        ExtractedMedicalData.patient_id == profile.id
    ).all()
    
    categories = {}
    for e in extracted:
        categories[e.data_category] = categories.get(e.data_category, 0) + 1
    
    # Calculate completeness
    expected_categories = ["demographics", "diagnosis", "treatment", "lab_results", "molecular"]
    completeness = (len(categories) / len(expected_categories)) * 100 if expected_categories else 0
    
    # Get last sync
    last_sync = None
    for c in connections:
        if c.last_sync and (not last_sync or c.last_sync > last_sync):
            last_sync = c.last_sync
    
    return PatientDataSummary(
        total_records=len(extracted),
        categories=categories,
        last_sync=last_sync,
        completeness_score=min(completeness, 100),
        connections=[
            MedicalConnectionResponse(
                id=str(c.id),
                source_type=c.source_type,
                source_name=c.source_name,
                connection_status=c.connection_status,
                last_sync=c.last_sync,
                records_synced=c.records_synced,
                created_at=c.created_at,
            )
            for c in connections
        ],
    )


@app.delete("/api/patient/connections/{connection_id}")
async def disconnect_medical_records(
    connection_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Disconnect a medical records source"""
    patient_repo = PatientRepository(db)
    profile = patient_repo.get_profile(UUID(token_data["sub"]))
    
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    connection = db.query(MedicalRecordConnection).filter(
        MedicalRecordConnection.id == connection_id,
        MedicalRecordConnection.patient_id == profile.id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection.connection_status = "disconnected"
    db.commit()
    
    return {
        "success": True,
        "message": "Medical records connection has been disconnected.",
    }


# ============== Data Marketplace Endpoints ==============

@app.get("/api/marketplace/products", response_model=List[DataProductSummary])
async def list_products(
    category: Optional[str] = None,
    cancer_type: Optional[str] = None,
    min_patients: int = 0,
    featured_only: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List available data products"""
    product_repo = DataProductRepository(db)
    products = product_repo.get_all(
        category=category,
        cancer_type=cancer_type,
        featured_only=featured_only,
        search=search,
    )

    # Filter by min patients
    if min_patients > 0:
        products = [p for p in products if (p.patient_count or 0) >= min_patients]

    return [
        DataProductSummary(
            id=str(p.id),
            name=p.name,
            description=p.description,
            cancer_types=p.cancer_types or [],
            patient_count=p.patient_count or 0,
            completeness_score=float(p.completeness_score or 0),
            price_from=float(min(p.pricing_tiers.values())) if p.pricing_tiers else 0,
            is_featured=p.is_featured,
        )
        for p in products
    ]


@app.get("/api/marketplace/products/{product_id}", response_model=DataProductDetail)
async def get_product_detail(product_id: str, db: Session = Depends(get_db)):
    """Get detailed product information"""
    product_repo = DataProductRepository(db)
    product = product_repo.get_by_id(UUID(product_id))

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return DataProductDetail(
        id=str(product.id),
        name=product.name,
        description=product.description,
        cancer_types=product.cancer_types or [],
        patient_count=product.patient_count or 0,
        record_count=product.record_count or 0,
        completeness_score=float(product.completeness_score or 0),
        data_categories=product.data_categories or [],
        date_range_start=product.date_range_start,
        date_range_end=product.date_range_end,
        price_from=float(min(product.pricing_tiers.values())) if product.pricing_tiers else 0,
        is_featured=product.is_featured,
        pricing_tiers={k: float(v) for k, v in (product.pricing_tiers or {}).items()},
        category=product.category,
    )


@app.post("/api/marketplace/inquiry")
async def submit_inquiry(
    product_id: str,
    contact: ContactRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Submit inquiry for a data product"""
    product_repo = DataProductRepository(db)
    product = product_repo.get_by_id(UUID(product_id))

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # TODO: Send email notification, create CRM record
    # background_tasks.add_task(send_inquiry_email, contact, product)

    return {
        "status": "success",
        "message": "Thank you for your inquiry. Our team will contact you within 24 hours.",
        "product_name": product.name,
    }


# ============== Cohort Builder Endpoints ==============

@app.post("/api/cohort/build", response_model=CohortResult)
async def build_cohort(
    criteria: CohortCriteria,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Build a patient cohort based on criteria"""
    cohort_repo = CohortRepository(db)

    # Convert criteria to dict
    criteria_dict = {
        "cancer_types": criteria.cancer_types,
        "stages": criteria.stages,
        "age_min": criteria.age_min,
        "age_max": criteria.age_max,
        "molecular_markers": criteria.molecular_markers,
        "treatment_types": criteria.treatment_types,
    }

    # Build cohort
    result = cohort_repo.build_cohort(criteria_dict)

    return CohortResult(
        patient_count=result["patient_count"],
        data_points=result["data_points"],
        diagnosis_count=result["diagnosis_count"],
        treatment_count=result["treatment_count"],
        molecular_count=result["molecular_count"],
    )


@app.post("/api/cohort/save")
async def save_cohort(
    request: SaveCohortRequest,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save a cohort for later use"""
    cohort_repo = CohortRepository(db)

    # Build cohort first to get count
    criteria_dict = request.criteria.dict()
    result = cohort_repo.build_cohort(criteria_dict)

    # Save cohort
    cohort = cohort_repo.save_cohort(
        user_id=UUID(token_data["sub"]),
        name=request.name,
        description=request.description,
        criteria=criteria_dict,
        patient_count=result["patient_count"],
    )

    return {
        "cohort_id": str(cohort.id),
        "name": cohort.name,
        "patient_count": cohort.patient_count,
    }


@app.get("/api/cohort/saved")
async def get_saved_cohorts(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get user's saved cohorts"""
    cohort_repo = CohortRepository(db)
    cohorts = cohort_repo.get_user_cohorts(UUID(token_data["sub"]))

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "patient_count": c.patient_count,
            "created_at": c.created_at.isoformat(),
        }
        for c in cohorts
    ]


@app.get("/api/cohort/{cohort_id}/summary")
async def get_cohort_summary(
    cohort_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get summary statistics for a cohort"""
    cohort_repo = CohortRepository(db)
    summary = cohort_repo.get_cohort_summary(UUID(cohort_id))

    if not summary:
        raise HTTPException(status_code=404, detail="Cohort not found")

    return summary


# ============== Study & Regulatory Endpoints ==============

@app.post("/api/researcher/studies", response_model=StudyResponse)
async def create_study(
    request: CreateStudyRequest,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new research study"""
    user_id = token_data["sub"]
    
    # Get cohort patient count if cohort_id provided
    patient_count = 0
    if request.cohort_id:
        cohort = db.query(ResearchCohort).filter(ResearchCohort.id == request.cohort_id).first()
        if cohort:
            patient_count = cohort.patient_count or 0
    
    study = Study(
        user_id=user_id,
        cohort_id=request.cohort_id,
        name=request.name,
        description=request.description,
        principal_investigator=request.principal_investigator,
        patient_count=patient_count,
        selected_variables=request.selected_variables,
        status="draft",
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    
    return StudyResponse(
        id=str(study.id),
        name=study.name,
        description=study.description,
        status=study.status,
        patient_count=study.patient_count,
        created_at=study.created_at,
        regulatory_status={},
    )


@app.get("/api/researcher/studies")
async def get_researcher_studies(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all studies for the current researcher"""
    user_id = token_data["sub"]
    
    studies = db.query(Study).filter(Study.user_id == user_id).order_by(Study.created_at.desc()).all()
    
    result = []
    for study in studies:
        # Get regulatory status
        submissions = db.query(RegulatorySubmission).filter(
            RegulatorySubmission.study_id == study.id
        ).all()
        
        reg_status = {}
        for sub in submissions:
            key = sub.document_type
            if sub.institution_id:
                inst = db.query(Institution).filter(Institution.id == sub.institution_id).first()
                if inst:
                    key = f"{sub.document_type}_{inst.name}"
            reg_status[key] = sub.status
        
        result.append({
            "id": str(study.id),
            "name": study.name,
            "description": study.description,
            "status": study.status,
            "patient_count": study.patient_count,
            "created_at": study.created_at.isoformat(),
            "regulatory_status": reg_status,
        })
    
    return result


@app.get("/api/researcher/studies/{study_id}")
async def get_study_detail(
    study_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get detailed study information including regulatory status"""
    study = db.query(Study).filter(Study.id == study_id).first()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get all regulatory submissions
    submissions = db.query(RegulatorySubmission).filter(
        RegulatorySubmission.study_id == study_id
    ).all()
    
    regulatory_items = []
    for sub in submissions:
        inst_name = None
        if sub.institution_id:
            inst = db.query(Institution).filter(Institution.id == sub.institution_id).first()
            if inst:
                inst_name = inst.name
        
        regulatory_items.append({
            "id": str(sub.id),
            "document_type": sub.document_type,
            "status": sub.status,
            "protocol_number": sub.protocol_number,
            "institution_name": inst_name,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "approved_at": sub.approved_at.isoformat() if sub.approved_at else None,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            "document_url": sub.document_url,
        })
    
    # Get extraction jobs
    jobs = db.query(ExtractionJob).filter(ExtractionJob.study_id == study_id).all()
    extraction_jobs = [
        {
            "id": str(job.id),
            "job_name": job.job_name,
            "status": job.status,
            "patient_count": job.patient_count,
            "variable_count": job.variable_count,
            "output_format": job.output_format,
            "estimated_completion": job.estimated_completion.isoformat() if job.estimated_completion else None,
            "download_url": job.download_url,
            "created_at": job.created_at.isoformat(),
        }
        for job in jobs
    ]
    
    return {
        "id": str(study.id),
        "name": study.name,
        "description": study.description,
        "status": study.status,
        "principal_investigator": study.principal_investigator,
        "patient_count": study.patient_count,
        "selected_variables": study.selected_variables,
        "created_at": study.created_at.isoformat(),
        "regulatory": regulatory_items,
        "extraction_jobs": extraction_jobs,
    }


@app.post("/api/regulatory/submit")
async def submit_regulatory(
    request: CreateRegulatoryRequest,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Submit a regulatory document (IRB protocol, DUA, or reliance agreement)"""
    study = db.query(Study).filter(Study.id == request.study_id).first()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Generate protocol number for IRB
    protocol_number = None
    if request.document_type == "irb_protocol":
        protocol_number = f"HDB-{datetime.utcnow().year}-{str(uuid.uuid4())[:8].upper()}"
    
    submission = RegulatorySubmission(
        study_id=request.study_id,
        institution_id=request.institution_id,
        document_type=request.document_type,
        status="submitted",
        protocol_number=protocol_number,
        submitted_at=datetime.utcnow(),
    )
    db.add(submission)
    
    # Update study status
    if study.status == "draft":
        study.status = "pending_approval"
    
    db.commit()
    db.refresh(submission)
    
    return {
        "success": True,
        "submission_id": str(submission.id),
        "document_type": submission.document_type,
        "status": submission.status,
        "protocol_number": submission.protocol_number,
        "message": f"{request.document_type.replace('_', ' ').title()} submitted successfully.",
    }


@app.post("/api/regulatory/{submission_id}/approve")
async def approve_regulatory(
    submission_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Approve a regulatory submission (admin endpoint)"""
    submission = db.query(RegulatorySubmission).filter(
        RegulatorySubmission.id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "approved"
    submission.approved_at = datetime.utcnow()
    
    # Set expiration (1 year for IRB, 2 years for DUA)
    if submission.document_type == "irb_protocol":
        submission.expires_at = datetime.utcnow() + timedelta(days=365)
    elif submission.document_type == "dua":
        submission.expires_at = datetime.utcnow() + timedelta(days=730)
    
    # Check if all required approvals are complete
    study = db.query(Study).filter(Study.id == submission.study_id).first()
    if study:
        all_submissions = db.query(RegulatorySubmission).filter(
            RegulatorySubmission.study_id == study.id
        ).all()
        
        all_approved = all(s.status in ["approved", "signed"] for s in all_submissions)
        if all_approved and len(all_submissions) >= 2:  # At least IRB and DUA
            study.status = "approved"
    
    db.commit()
    
    return {
        "success": True,
        "message": "Submission approved.",
        "expires_at": submission.expires_at.isoformat() if submission.expires_at else None,
    }


@app.post("/api/extraction/create")
async def create_extraction_job(
    request: ExtractionJobRequest,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a data extraction job"""
    study = db.query(Study).filter(Study.id == request.study_id).first()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Check if study has all required approvals
    submissions = db.query(RegulatorySubmission).filter(
        RegulatorySubmission.study_id == request.study_id
    ).all()
    
    irb_approved = any(s.document_type == "irb_protocol" and s.status == "approved" for s in submissions)
    dua_signed = any(s.document_type == "dua" and s.status in ["approved", "signed"] for s in submissions)
    
    if not irb_approved or not dua_signed:
        raise HTTPException(
            status_code=400,
            detail="Cannot extract data without IRB approval and signed DUA"
        )
    
    # Create extraction job
    job_name = f"extract_{study.name.lower().replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}"
    estimated_completion = datetime.utcnow() + timedelta(days=2)  # Estimate 2 days
    
    job = ExtractionJob(
        study_id=request.study_id,
        job_name=job_name,
        status="queued",
        patient_count=study.patient_count,
        variable_count=len(request.variables),
        output_format=request.output_format,
        deidentification_level=request.deidentification_level,
        estimated_completion=estimated_completion,
    )
    db.add(job)
    
    # Update study status
    study.status = "active"
    
    db.commit()
    db.refresh(job)
    
    return {
        "success": True,
        "job_id": str(job.id),
        "job_name": job.job_name,
        "status": job.status,
        "patient_count": job.patient_count,
        "variable_count": job.variable_count,
        "estimated_completion": estimated_completion.isoformat(),
        "message": "Extraction job queued. You will be notified when data is ready.",
    }


@app.get("/api/extraction/jobs")
async def get_extraction_jobs(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all extraction jobs for the current user's studies"""
    user_id = token_data["sub"]
    
    # Get user's studies
    studies = db.query(Study).filter(Study.user_id == user_id).all()
    study_ids = [str(s.id) for s in studies]
    
    jobs = db.query(ExtractionJob).filter(
        ExtractionJob.study_id.in_(study_ids)
    ).order_by(ExtractionJob.created_at.desc()).all()
    
    return [
        {
            "id": str(job.id),
            "job_name": job.job_name,
            "status": job.status,
            "patient_count": job.patient_count,
            "variable_count": job.variable_count,
            "output_format": job.output_format,
            "estimated_completion": job.estimated_completion.isoformat() if job.estimated_completion else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "download_url": job.download_url,
            "created_at": job.created_at.isoformat(),
        }
        for job in jobs
    ]


@app.get("/api/emr/connections")
async def get_emr_connections(
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all EMR connections and their status"""
    connections = db.query(EMRConnection).all()
    
    result = []
    for conn in connections:
        inst = db.query(Institution).filter(Institution.id == conn.institution_id).first()
        result.append({
            "id": str(conn.id),
            "institution_name": inst.name if inst else "Unknown",
            "emr_vendor": conn.emr_vendor,
            "connection_type": conn.connection_type,
            "status": conn.status,
            "last_sync": conn.last_sync.isoformat() if conn.last_sync else None,
            "patient_count": conn.patient_count,
            "data_completeness_score": conn.data_completeness_score,
        })
    
    return result


@app.get("/api/institutions")
async def get_institutions(
    db: Session = Depends(get_db)
):
    """Get all partner institutions"""
    institutions = db.query(Institution).filter(Institution.is_active == True).all()
    
    return [
        {
            "id": str(inst.id),
            "name": inst.name,
            "type": inst.type,
            "city": inst.city,
            "state": inst.state,
            "emr_system": inst.emr_system,
        }
        for inst in institutions
    ]


# ============== Collaboration Endpoints ==============

@app.get("/api/study/{study_id}/team")
async def get_study_team(
    study_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all collaborators on a study"""
    collaborators = db.query(StudyCollaborator).filter(
        StudyCollaborator.study_id == study_id
    ).all()
    
    result = []
    for collab in collaborators:
        user_info = None
        if collab.user_id:
            user = db.query(User).filter(User.id == collab.user_id).first()
            if user:
                user_info = {"name": user.name, "email": user.email, "organization": user.organization}
        
        result.append({
            "id": str(collab.id),
            "email": collab.email,
            "role": collab.role,
            "status": collab.status,
            "permissions": collab.permissions,
            "user": user_info,
            "invited_at": collab.invited_at.isoformat() if collab.invited_at else None,
            "accepted_at": collab.accepted_at.isoformat() if collab.accepted_at else None,
        })
    
    return result


@app.post("/api/study/{study_id}/invite")
async def invite_collaborator(
    study_id: str,
    email: str,
    role: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Invite a collaborator to a study"""
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Check if user is PI
    if study.user_id != token_data["sub"]:
        raise HTTPException(status_code=403, detail="Only the PI can invite collaborators")
    
    # Check if already invited
    existing = db.query(StudyCollaborator).filter(
        StudyCollaborator.study_id == study_id,
        StudyCollaborator.email == email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="This email has already been invited")
    
    # Set permissions based on role
    permissions = {}
    if role == "co_investigator":
        permissions = {"data_access": True, "run_queries": True, "export": True, "edit_study": False}
    elif role == "analyst":
        permissions = {"data_access": True, "run_queries": True, "export": False, "edit_study": False}
    elif role == "statistician":
        permissions = {"data_access": True, "run_queries": True, "export": True, "edit_study": False}
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    collaborator = StudyCollaborator(
        study_id=study_id,
        user_id=str(user.id) if user else None,
        email=email,
        role=role,
        status="invited" if not user else "accepted",  # Auto-accept if user exists
        permissions=permissions,
        accepted_at=datetime.utcnow() if user else None,
    )
    db.add(collaborator)
    db.commit()
    
    return {
        "success": True,
        "collaborator_id": str(collaborator.id),
        "status": collaborator.status,
        "message": f"Invitation sent to {email}",
    }


@app.post("/api/study/{study_id}/comments")
async def add_study_comment(
    study_id: str,
    content: str,
    parent_id: Optional[str] = None,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add a comment to a study discussion"""
    comment = StudyComment(
        study_id=study_id,
        user_id=token_data["sub"],
        parent_id=parent_id,
        content=content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return {
        "success": True,
        "comment_id": str(comment.id),
        "created_at": comment.created_at.isoformat(),
    }


@app.get("/api/study/{study_id}/comments")
async def get_study_comments(
    study_id: str,
    token_data: Dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all comments on a study"""
    comments = db.query(StudyComment).filter(
        StudyComment.study_id == study_id
    ).order_by(StudyComment.created_at.desc()).all()
    
    result = []
    for comment in comments:
        user = db.query(User).filter(User.id == comment.user_id).first()
        result.append({
            "id": str(comment.id),
            "content": comment.content,
            "parent_id": comment.parent_id,
            "is_resolved": comment.is_resolved,
            "user": {"name": user.name if user else "Unknown", "email": user.email if user else None},
            "created_at": comment.created_at.isoformat(),
        })
    
    return result


@app.get("/api/diseases/variable-sets")
async def get_disease_variable_sets(
    db: Session = Depends(get_db)
):
    """Get pre-defined variable sets for diseases"""
    # Check if variable sets exist, if not create defaults
    sets = db.query(DiseaseVariableSet).filter(DiseaseVariableSet.is_active == True).all()
    
    if not sets:
        # Create default disease variable sets
        default_sets = [
            {
                "disease_name": "Multiple Myeloma",
                "icd10_codes": ["C90.0", "C90.1", "C90.2"],
                "core_variables": ["age_at_diagnosis", "sex", "race", "insurance_type"],
                "staging_variables": ["iss_stage", "riss_stage", "bone_lesions", "extramedullary_disease"],
                "molecular_variables": ["del_17p", "t_4_14", "t_14_16", "t_11_14", "gain_1q", "hyperdiploidy"],
                "treatment_variables": ["regimen_name", "line_of_therapy", "start_date", "cycles_completed", "dose_modifications"],
                "outcome_variables": ["best_response", "pfs_months", "os_months", "mrd_status", "time_to_next_treatment"],
            },
            {
                "disease_name": "Diffuse Large B-Cell Lymphoma",
                "icd10_codes": ["C83.3"],
                "core_variables": ["age_at_diagnosis", "sex", "race", "ecog_status"],
                "staging_variables": ["ann_arbor_stage", "ipi_score", "bulk_disease"],
                "molecular_variables": ["cell_of_origin", "bcl2_rearrangement", "myc_rearrangement", "double_hit"],
                "treatment_variables": ["regimen_name", "cycles_completed", "radiation_received"],
                "outcome_variables": ["complete_response", "event_free_survival", "overall_survival"],
            },
            {
                "disease_name": "Acute Myeloid Leukemia",
                "icd10_codes": ["C92.0", "C92.4", "C92.5"],
                "core_variables": ["age_at_diagnosis", "sex", "race", "wbc_at_diagnosis"],
                "staging_variables": ["eln_risk_group", "secondary_aml", "therapy_related"],
                "molecular_variables": ["flt3_itd", "flt3_tkd", "npm1", "idh1", "idh2", "tp53", "runx1"],
                "treatment_variables": ["induction_regimen", "consolidation", "transplant_type"],
                "outcome_variables": ["complete_remission", "relapse", "overall_survival", "relapse_free_survival"],
            },
        ]
        
        for ds in default_sets:
            disease_set = DiseaseVariableSet(**ds)
            db.add(disease_set)
        db.commit()
        
        sets = db.query(DiseaseVariableSet).filter(DiseaseVariableSet.is_active == True).all()
    
    return [
        {
            "id": str(s.id),
            "disease_name": s.disease_name,
            "icd10_codes": s.icd10_codes,
            "core_variables": s.core_variables,
            "staging_variables": s.staging_variables,
            "molecular_variables": s.molecular_variables,
            "treatment_variables": s.treatment_variables,
            "outcome_variables": s.outcome_variables,
        }
        for s in sets
    ]


@app.get("/api/diseases/{disease_name}/variables")
async def get_disease_variables(
    disease_name: str,
    db: Session = Depends(get_db)
):
    """Get variables for a specific disease"""
    disease_set = db.query(DiseaseVariableSet).filter(
        DiseaseVariableSet.disease_name.ilike(f"%{disease_name}%")
    ).first()
    
    if not disease_set:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    # Combine all variables
    all_variables = {
        "demographics": disease_set.core_variables or [],
        "staging": disease_set.staging_variables or [],
        "molecular": disease_set.molecular_variables or [],
        "treatment": disease_set.treatment_variables or [],
        "outcomes": disease_set.outcome_variables or [],
    }
    
    return {
        "disease_name": disease_set.disease_name,
        "icd10_codes": disease_set.icd10_codes,
        "variables": all_variables,
        "total_variable_count": sum(len(v) for v in all_variables.values()),
    }


# ============== Stats & Analytics Endpoints ==============

@app.get("/api/stats/platform")
async def get_platform_stats(db: Session = Depends(get_db)):
    """Get public platform statistics"""
    clinical_repo = ClinicalDataRepository(db)
    stats = clinical_repo.get_platform_stats()

    return {
        "total_patients": stats["total_patients"],
        "total_data_points": stats["total_data_points"],
        "active_studies": stats["active_studies"],
        "partner_institutions": stats["partner_institutions"],
        "cancer_types_covered": stats["cancer_types_covered"],
        "countries": 12,  # Would come from institution data
    }


@app.get("/api/stats/cancer-types")
async def get_cancer_type_stats(db: Session = Depends(get_db)):
    """Get statistics by cancer type"""
    clinical_repo = ClinicalDataRepository(db)
    stats = clinical_repo.get_cancer_type_stats()

    return stats


# ============== Contact & Support Endpoints ==============

@app.post("/api/contact")
async def submit_contact(
    contact: ContactRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit contact form"""
    # TODO: Store in database, send email
    # background_tasks.add_task(send_contact_email, contact)

    return {
        "status": "success",
        "message": "Thank you for reaching out. We'll respond within 24 hours.",
    }


# ============== Health Check ==============

@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": db_status,
    }


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
