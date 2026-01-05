"""
Base EMR Connector with common interface for all EMR systems
Supports FHIR R4, HL7 v2, and proprietary APIs
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Generator
from enum import Enum
import logging
import hashlib
from functools import lru_cache

logger = logging.getLogger(__name__)


class EMRType(Enum):
    EPIC = "epic"
    CERNER = "cerner"
    MEDITECH = "meditech"
    ALLSCRIPTS = "allscripts"
    ATHENA = "athena"
    NEXTGEN = "nextgen"
    CUSTOM_FHIR = "custom_fhir"
    CUSTOM_HL7 = "custom_hl7"


class DataCategory(Enum):
    DEMOGRAPHICS = "demographics"
    DIAGNOSES = "diagnoses"
    PROCEDURES = "procedures"
    MEDICATIONS = "medications"
    LABS = "labs"
    VITALS = "vitals"
    PATHOLOGY = "pathology"
    RADIOLOGY = "radiology"
    NOTES = "notes"
    GENOMICS = "genomics"


@dataclass
class ConnectionConfig:
    """EMR connection configuration"""
    emr_type: EMRType
    base_url: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    database_connection_string: Optional[str] = None
    fhir_version: str = "R4"
    hl7_version: str = "2.5"
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatientQuery:
    """Query parameters for patient data extraction"""
    mrns: Optional[List[str]] = None  # List of MRNs to query
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    data_categories: List[DataCategory] = field(default_factory=list)
    diagnosis_codes: Optional[List[str]] = None  # ICD codes to filter by
    include_deceased: bool = True
    batch_size: int = 100


@dataclass
class ExtractedRecord:
    """Standardized extracted record from EMR"""
    source_emr: EMRType
    source_id: str  # Original ID in EMR
    mrn: str  # Will be hashed before storage
    category: DataCategory
    record_date: datetime
    data: Dict[str, Any]
    raw_data: Optional[Dict[str, Any]] = None  # Original format for audit
    metadata: Dict[str, Any] = field(default_factory=dict)


class EMRConnector(ABC):
    """
    Abstract base class for EMR connectors.
    All EMR integrations must implement this interface.
    """
    
    def __init__(self, config: ConnectionConfig, salt: str):
        self.config = config
        self.salt = salt
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to EMR system"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to EMR system"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status"""
        pass
    
    @abstractmethod
    async def extract_patients(
        self, 
        query: PatientQuery
    ) -> Generator[ExtractedRecord, None, None]:
        """Extract patient records based on query parameters"""
        pass
    
    @abstractmethod
    async def get_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        """Get a single patient by MRN"""
        pass
    
    def hash_mrn(self, mrn: str) -> str:
        """Hash MRN using SHA-256 with salt for de-identification"""
        salted = f"{mrn}-{self.salt}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()
    
    def _normalize_date(self, date_str: str) -> Optional[date]:
        """Normalize date strings from various EMR formats"""
        formats = [
            "%Y-%m-%d",
            "%Y%m%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _normalize_icd_code(self, code: str) -> str:
        """Normalize ICD codes to consistent format"""
        # Remove dots and spaces, uppercase
        normalized = code.replace(".", "").replace(" ", "").upper()
        # Re-add dot in correct position for ICD-10
        if len(normalized) > 3:
            normalized = normalized[:3] + "." + normalized[3:]
        return normalized


class FHIRResourceMapper:
    """
    Maps FHIR R4 resources to HealthDB data structures
    """
    
    RESOURCE_TO_CATEGORY = {
        "Patient": DataCategory.DEMOGRAPHICS,
        "Condition": DataCategory.DIAGNOSES,
        "Procedure": DataCategory.PROCEDURES,
        "MedicationRequest": DataCategory.MEDICATIONS,
        "MedicationAdministration": DataCategory.MEDICATIONS,
        "Observation": DataCategory.LABS,  # Can also be vitals
        "DiagnosticReport": DataCategory.PATHOLOGY,
        "DocumentReference": DataCategory.NOTES,
        "ImagingStudy": DataCategory.RADIOLOGY,
    }
    
    @classmethod
    def map_patient(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR Patient resource to HealthDB format"""
        name = resource.get("name", [{}])[0]
        return {
            "mrn": cls._extract_mrn(resource),
            "family_name": name.get("family", ""),
            "given_names": name.get("given", []),
            "birth_date": resource.get("birthDate"),
            "gender": resource.get("gender"),
            "deceased": resource.get("deceasedBoolean", False),
            "deceased_date": resource.get("deceasedDateTime"),
            "race": cls._extract_extension(resource, "us-core-race"),
            "ethnicity": cls._extract_extension(resource, "us-core-ethnicity"),
        }
    
    @classmethod
    def map_condition(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR Condition resource to HealthDB diagnosis format"""
        code = resource.get("code", {}).get("coding", [{}])[0]
        return {
            "icd_code": code.get("code", ""),
            "description": code.get("display", ""),
            "coding_system": code.get("system", ""),
            "clinical_status": resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code"),
            "verification_status": resource.get("verificationStatus", {}).get("coding", [{}])[0].get("code"),
            "onset_date": resource.get("onsetDateTime"),
            "recorded_date": resource.get("recordedDate"),
            "stage": cls._extract_stage(resource),
        }
    
    @classmethod
    def map_medication(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR MedicationRequest to HealthDB format"""
        medication = resource.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
        dosage = resource.get("dosageInstruction", [{}])[0]
        return {
            "medication_code": medication.get("code", ""),
            "medication_name": medication.get("display", ""),
            "coding_system": medication.get("system", ""),
            "status": resource.get("status"),
            "intent": resource.get("intent"),
            "authored_on": resource.get("authoredOn"),
            "dosage_text": dosage.get("text", ""),
            "route": dosage.get("route", {}).get("text", ""),
        }
    
    @classmethod
    def map_observation(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR Observation to HealthDB lab/vital format"""
        code = resource.get("code", {}).get("coding", [{}])[0]
        value = cls._extract_observation_value(resource)
        return {
            "loinc_code": code.get("code", ""),
            "test_name": code.get("display", ""),
            "value": value.get("value"),
            "unit": value.get("unit"),
            "value_string": value.get("string"),
            "reference_range": cls._extract_reference_range(resource),
            "status": resource.get("status"),
            "effective_date": resource.get("effectiveDateTime"),
            "category": cls._extract_observation_category(resource),
        }
    
    @classmethod
    def map_diagnostic_report(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR DiagnosticReport to HealthDB pathology format"""
        code = resource.get("code", {}).get("coding", [{}])[0]
        return {
            "report_code": code.get("code", ""),
            "report_name": code.get("display", ""),
            "status": resource.get("status"),
            "effective_date": resource.get("effectiveDateTime"),
            "issued_date": resource.get("issued"),
            "conclusion": resource.get("conclusion", ""),
            "presented_form": cls._extract_presented_form(resource),
        }
    
    @staticmethod
    def _extract_mrn(patient: Dict[str, Any]) -> Optional[str]:
        """Extract MRN from patient identifiers"""
        for identifier in patient.get("identifier", []):
            type_coding = identifier.get("type", {}).get("coding", [{}])[0]
            if type_coding.get("code") == "MR":
                return identifier.get("value")
        return None
    
    @staticmethod
    def _extract_extension(resource: Dict[str, Any], extension_name: str) -> Optional[str]:
        """Extract value from FHIR extension"""
        for ext in resource.get("extension", []):
            if extension_name in ext.get("url", ""):
                return ext.get("valueString") or ext.get("valueCoding", {}).get("display")
        return None
    
    @staticmethod
    def _extract_stage(condition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract cancer staging from condition resource"""
        stage_data = condition.get("stage", [{}])[0]
        if not stage_data:
            return None
        summary = stage_data.get("summary", {}).get("coding", [{}])[0]
        return {
            "stage": summary.get("code", ""),
            "display": summary.get("display", ""),
            "system": summary.get("system", ""),
        }
    
    @staticmethod
    def _extract_observation_value(observation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract value from observation (handles different value types)"""
        if "valueQuantity" in observation:
            qty = observation["valueQuantity"]
            return {"value": qty.get("value"), "unit": qty.get("unit")}
        elif "valueString" in observation:
            return {"string": observation["valueString"]}
        elif "valueCodeableConcept" in observation:
            coding = observation["valueCodeableConcept"].get("coding", [{}])[0]
            return {"string": coding.get("display", coding.get("code", ""))}
        return {}
    
    @staticmethod
    def _extract_reference_range(observation: Dict[str, Any]) -> Optional[str]:
        """Extract reference range from observation"""
        ranges = observation.get("referenceRange", [{}])[0]
        low = ranges.get("low", {}).get("value")
        high = ranges.get("high", {}).get("value")
        if low is not None and high is not None:
            return f"{low}-{high}"
        return ranges.get("text")
    
    @staticmethod
    def _extract_observation_category(observation: Dict[str, Any]) -> Optional[str]:
        """Determine if observation is lab, vital, etc."""
        for cat in observation.get("category", []):
            coding = cat.get("coding", [{}])[0]
            if coding.get("code") == "vital-signs":
                return "vital"
            elif coding.get("code") == "laboratory":
                return "lab"
        return "other"
    
    @staticmethod
    def _extract_presented_form(report: Dict[str, Any]) -> Optional[str]:
        """Extract report content from presentedForm"""
        forms = report.get("presentedForm", [])
        for form in forms:
            if form.get("contentType") == "text/plain":
                return form.get("data")  # Base64 encoded
        return None

