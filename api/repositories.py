"""
HealthDB Repositories
Database access layer for all entities
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib

from .models import (
    User, Institution, PatientProfile, Consent,
    RewardsTransaction, CancerDiagnosis, Treatment, TreatmentResponse,
    MolecularData, Outcome, DataProduct, DataPurchase, DataAccessLog,
    ResearchCohort
)


# ============== User Repository ==============

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == str(user_id)).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password_hash: str, name: str,
               user_type: str, organization: Optional[str] = None) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            user_type=user_type,
            organization=organization,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user_id: str) -> None:
        self.db.query(User).filter(User.id == str(user_id)).update(
            {"last_login": datetime.utcnow()}
        )
        self.db.commit()

    def verify_user(self, user_id: str) -> None:
        self.db.query(User).filter(User.id == str(user_id)).update(
            {"is_verified": True}
        )
        self.db.commit()


# ============== Patient Repository ==============

class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: str) -> Optional[PatientProfile]:
        return self.db.query(PatientProfile).filter(
            PatientProfile.user_id == str(user_id)
        ).first()

    def create_profile(self, user_id: str, hashed_mrn: Optional[str] = None) -> PatientProfile:
        profile = PatientProfile(
            user_id=str(user_id),
            hashed_mrn=hashed_mrn,
            points_balance=100,  # Welcome bonus
            total_points_earned=100,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        # Log welcome bonus
        self.add_reward_transaction(
            profile.id, "earn", 100, "Welcome bonus for joining HealthDB"
        )
        return profile

    def get_consents(self, patient_id: str) -> List[Consent]:
        return self.db.query(Consent).filter(
            Consent.patient_id == str(patient_id)
        ).order_by(Consent.created_at.desc()).all()

    def create_consent(self, patient_id: str, consent_type: str,
                       consent_options: Dict, signature: str,
                       ip_address: Optional[str] = None) -> Consent:
        consent = Consent(
            patient_id=str(patient_id),
            consent_type=consent_type,
            consent_version="1.0",
            status="active",
            consent_options=consent_options,
            signed_date=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            signature=signature,
            ip_address=ip_address,
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)

        # Award points for signing consent
        profile = self.db.query(PatientProfile).filter(
            PatientProfile.id == str(patient_id)
        ).first()
        if profile:
            self.add_points(patient_id, 50, f"Signed {consent_type} consent")

        return consent

    def revoke_consent(self, consent_id: str) -> None:
        self.db.query(Consent).filter(Consent.id == str(consent_id)).update({
            "status": "revoked",
            "revoked_at": datetime.utcnow(),
        })
        self.db.commit()

    def get_rewards_history(self, patient_id: str, limit: int = 50) -> List[RewardsTransaction]:
        return self.db.query(RewardsTransaction).filter(
            RewardsTransaction.patient_id == str(patient_id)
        ).order_by(RewardsTransaction.created_at.desc()).limit(limit).all()

    def add_points(self, patient_id: str, points: int, description: str,
                   reference_type: Optional[str] = None, reference_id: Optional[str] = None) -> None:
        # Update balance
        self.db.query(PatientProfile).filter(PatientProfile.id == str(patient_id)).update({
            "points_balance": PatientProfile.points_balance + points,
            "total_points_earned": PatientProfile.total_points_earned + points,
        })

        # Log transaction
        self.add_reward_transaction(patient_id, "earn", points, description, reference_type, reference_id)
        self.db.commit()

    def add_reward_transaction(self, patient_id: str, transaction_type: str,
                                points: int, description: str,
                                reference_type: Optional[str] = None,
                                reference_id: Optional[str] = None) -> None:
        transaction = RewardsTransaction(
            patient_id=str(patient_id),
            transaction_type=transaction_type,
            points=points,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(transaction)

    def get_data_access_log(self, patient_id: str, limit: int = 50) -> List[DataAccessLog]:
        return self.db.query(DataAccessLog).filter(
            DataAccessLog.patient_id == str(patient_id)
        ).order_by(DataAccessLog.created_at.desc()).limit(limit).all()

    def get_studies_count(self, patient_id: str) -> int:
        return self.db.query(func.count(DataAccessLog.id)).filter(
            DataAccessLog.patient_id == str(patient_id)
        ).scalar() or 0


# ============== Clinical Data Repository ==============

class ClinicalDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_diagnosis_by_id(self, diagnosis_id: str) -> Optional[CancerDiagnosis]:
        return self.db.query(CancerDiagnosis).filter(
            CancerDiagnosis.id == str(diagnosis_id)
        ).first()

    def get_diagnoses_by_patient(self, hashed_patient_id: str) -> List[CancerDiagnosis]:
        return self.db.query(CancerDiagnosis).filter(
            CancerDiagnosis.hashed_patient_id == hashed_patient_id
        ).order_by(CancerDiagnosis.diagnosis_date.desc()).all()

    def create_diagnosis(self, data: Dict[str, Any]) -> CancerDiagnosis:
        diagnosis = CancerDiagnosis(**data)
        self.db.add(diagnosis)
        self.db.commit()
        self.db.refresh(diagnosis)
        return diagnosis

    def create_treatment(self, diagnosis_id: str, data: Dict[str, Any]) -> Treatment:
        treatment = Treatment(diagnosis_id=str(diagnosis_id), **data)
        self.db.add(treatment)
        self.db.commit()
        self.db.refresh(treatment)
        return treatment

    def create_response(self, treatment_id: str, data: Dict[str, Any]) -> TreatmentResponse:
        response = TreatmentResponse(treatment_id=str(treatment_id), **data)
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def create_molecular_data(self, diagnosis_id: str, data: Dict[str, Any]) -> MolecularData:
        molecular = MolecularData(diagnosis_id=str(diagnosis_id), **data)
        self.db.add(molecular)
        self.db.commit()
        self.db.refresh(molecular)
        return molecular

    def get_cancer_type_stats(self) -> List[Dict]:
        """Get patient counts by cancer type"""
        results = self.db.query(
            CancerDiagnosis.cancer_type,
            func.count(func.distinct(CancerDiagnosis.hashed_patient_id)).label("patient_count")
        ).group_by(CancerDiagnosis.cancer_type).order_by(
            func.count(func.distinct(CancerDiagnosis.hashed_patient_id)).desc()
        ).all()

        return [{"name": r[0], "patients": r[1]} for r in results]

    def get_platform_stats(self) -> Dict[str, int]:
        """Get overall platform statistics"""
        total_patients = self.db.query(
            func.count(func.distinct(CancerDiagnosis.hashed_patient_id))
        ).scalar() or 0

        total_diagnoses = self.db.query(func.count(CancerDiagnosis.id)).scalar() or 0
        total_treatments = self.db.query(func.count(Treatment.id)).scalar() or 0
        total_molecular = self.db.query(func.count(MolecularData.id)).scalar() or 0

        cancer_types = self.db.query(
            func.count(func.distinct(CancerDiagnosis.cancer_type))
        ).scalar() or 0

        institutions = self.db.query(
            func.count(func.distinct(CancerDiagnosis.institution_id))
        ).scalar() or 0

        return {
            "total_patients": total_patients,
            "total_data_points": total_diagnoses + total_treatments + total_molecular,
            "cancer_types_covered": cancer_types,
            "partner_institutions": institutions,
            "active_studies": self.db.query(func.count(ResearchCohort.id)).filter(
                ResearchCohort.is_saved == True
            ).scalar() or 0,
        }


# ============== Cohort Builder Repository ==============

class CohortRepository:
    def __init__(self, db: Session):
        self.db = db

    def build_cohort(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Build a cohort based on criteria and return statistics"""
        query = self.db.query(CancerDiagnosis)

        # Apply filters
        if criteria.get("cancer_types"):
            query = query.filter(CancerDiagnosis.cancer_type.in_(criteria["cancer_types"]))

        if criteria.get("stages"):
            query = query.filter(CancerDiagnosis.stage.in_(criteria["stages"]))

        if criteria.get("age_min") or criteria.get("age_max"):
            # Age calculation would require date of birth - simplified for now
            pass

        if criteria.get("molecular_markers"):
            markers = criteria["molecular_markers"]
            diagnosis_ids = self.db.query(MolecularData.diagnosis_id).filter(
                MolecularData.gene.in_(markers)
            ).distinct()
            query = query.filter(CancerDiagnosis.id.in_(diagnosis_ids))

        if criteria.get("treatment_types"):
            treatment_types = [TreatmentType(t) for t in criteria["treatment_types"] if t in TreatmentType.__members__.values()]
            if treatment_types:
                diagnosis_ids = self.db.query(Treatment.diagnosis_id).filter(
                    Treatment.treatment_type.in_(treatment_types)
                ).distinct()
                query = query.filter(CancerDiagnosis.id.in_(diagnosis_ids))

        # Get results
        diagnoses = query.all()
        patient_ids = set(d.hashed_patient_id for d in diagnoses)

        # Calculate statistics
        patient_count = len(patient_ids)
        data_points = len(diagnoses)

        # Get treatment count for these diagnoses
        treatment_count = self.db.query(func.count(Treatment.id)).filter(
            Treatment.diagnosis_id.in_([d.id for d in diagnoses])
        ).scalar() or 0

        # Get molecular data count
        molecular_count = self.db.query(func.count(MolecularData.id)).filter(
            MolecularData.diagnosis_id.in_([d.id for d in diagnoses])
        ).scalar() or 0

        return {
            "patient_count": patient_count,
            "data_points": data_points + treatment_count + molecular_count,
            "diagnosis_count": len(diagnoses),
            "treatment_count": treatment_count,
            "molecular_count": molecular_count,
        }

    def save_cohort(self, user_id: str, name: str, description: str,
                    criteria: Dict, patient_count: int) -> ResearchCohort:
        cohort = ResearchCohort(
            user_id=str(user_id),
            name=name,
            description=description,
            criteria=criteria,
            patient_count=patient_count,
            is_saved=True,
        )
        self.db.add(cohort)
        self.db.commit()
        self.db.refresh(cohort)
        return cohort

    def get_user_cohorts(self, user_id: str) -> List[ResearchCohort]:
        return self.db.query(ResearchCohort).filter(
            ResearchCohort.user_id == str(user_id),
            ResearchCohort.is_saved == True,
        ).order_by(ResearchCohort.created_at.desc()).all()

    def get_cohort_summary(self, cohort_id: str) -> Dict[str, Any]:
        """Get detailed summary for a saved cohort"""
        cohort = self.db.query(ResearchCohort).filter(
            ResearchCohort.id == str(cohort_id)
        ).first()

        if not cohort:
            return {}

        # Rebuild cohort stats
        stats = self.build_cohort(cohort.criteria)

        # Get demographics
        # This would require more detailed patient data

        return {
            "cohort_id": str(cohort.id),
            "name": cohort.name,
            **stats,
        }


# ============== Data Product Repository ==============

class DataProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, category: Optional[str] = None,
                cancer_type: Optional[str] = None,
                featured_only: bool = False,
                search: Optional[str] = None) -> List[DataProduct]:
        query = self.db.query(DataProduct).filter(DataProduct.is_active == True)

        if featured_only:
            query = query.filter(DataProduct.is_featured == True)

        if category:
            query = query.filter(DataProduct.category == category)

        if cancer_type:
            query = query.filter(
                DataProduct.cancer_types.contains([cancer_type])
            )

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DataProduct.name.ilike(search_pattern),
                    DataProduct.description.ilike(search_pattern),
                )
            )

        return query.order_by(DataProduct.is_featured.desc(), DataProduct.created_at.desc()).all()

    def get_by_id(self, product_id: str) -> Optional[DataProduct]:
        return self.db.query(DataProduct).filter(
            DataProduct.id == str(product_id),
            DataProduct.is_active == True,
        ).first()

    def create(self, data: Dict[str, Any]) -> DataProduct:
        product = DataProduct(**data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_stats(self, product_id: str) -> None:
        """Update patient count and record count based on actual data"""
        product = self.get_by_id(product_id)
        if not product:
            return

        # Get counts based on cancer types in product
        if product.cancer_types:
            patient_count = self.db.query(
                func.count(func.distinct(CancerDiagnosis.hashed_patient_id))
            ).filter(
                CancerDiagnosis.cancer_type.in_(product.cancer_types)
            ).scalar() or 0

            record_count = self.db.query(func.count(CancerDiagnosis.id)).filter(
                CancerDiagnosis.cancer_type.in_(product.cancer_types)
            ).scalar() or 0

            self.db.query(DataProduct).filter(DataProduct.id == str(product_id)).update({
                "patient_count": patient_count,
                "record_count": record_count,
            })
            self.db.commit()


# ============== Data Access Log Repository ==============

class DataAccessLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_access(self, user_id: str, patient_id: Optional[str],
                   product_id: Optional[str], access_type: str,
                   data_type: str, purpose: str, record_count: int,
                   ip_address: Optional[str] = None) -> DataAccessLog:
        log = DataAccessLog(
            user_id=str(user_id) if user_id else None,
            patient_id=str(patient_id) if patient_id else None,
            product_id=str(product_id) if product_id else None,
            access_type=access_type,
            data_type=data_type,
            purpose=purpose,
            record_count=record_count,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        # Award points to patient if applicable
        if patient_id:
            patient_repo = PatientRepository(self.db)
            patient_repo.add_points(
                patient_id, 50,
                f"Data accessed for {purpose}",
                "data_access", log.id
            )

        return log

