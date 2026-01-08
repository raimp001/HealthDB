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
import os
from jose import jwt
import hashlib

from sqlalchemy.orm import Session

from sqlalchemy import text
from .database import get_db, init_db, engine
from .models import (
    Base, User, PatientProfile, Consent,
    CancerDiagnosis, Treatment, DataProduct, DataAccessLog, ResearchCohort
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
    """Initialize database and seed data on startup"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial data if tables are empty
    db = next(get_db())
    try:
        from .seed import seed_institutions, seed_data_products
        
        # Check if data products exist
        product_count = db.query(DataProduct).count()
        if product_count == 0:
            print("Seeding initial data...")
            seed_institutions(db)
            seed_data_products(db)
            print("Seeding complete!")
    except Exception as e:
        print(f"Seed error (may be normal on first run): {e}")
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
