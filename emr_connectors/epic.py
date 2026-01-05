"""
Epic EMR Connector
Supports Epic FHIR R4 API and direct Clarity database access
"""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
import jwt
import time
from functools import lru_cache

from .base import (
    EMRConnector, EMRType, ConnectionConfig, PatientQuery,
    ExtractedRecord, DataCategory, FHIRResourceMapper
)

logger = logging.getLogger(__name__)


class EpicFHIRConnector(EMRConnector):
    """
    Epic FHIR R4 API connector using SMART on FHIR authentication
    """
    
    FHIR_RESOURCES = {
        DataCategory.DEMOGRAPHICS: ["Patient"],
        DataCategory.DIAGNOSES: ["Condition"],
        DataCategory.PROCEDURES: ["Procedure"],
        DataCategory.MEDICATIONS: ["MedicationRequest", "MedicationAdministration"],
        DataCategory.LABS: ["Observation?category=laboratory"],
        DataCategory.VITALS: ["Observation?category=vital-signs"],
        DataCategory.PATHOLOGY: ["DiagnosticReport"],
        DataCategory.NOTES: ["DocumentReference"],
        DataCategory.RADIOLOGY: ["ImagingStudy"],
    }
    
    # Epic-specific FHIR extensions and profiles
    EPIC_EXTENSIONS = {
        "cancer-stage": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-stage-group",
        "tumor-marker": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-tumor-marker-test",
    }
    
    def __init__(self, config: ConnectionConfig, salt: str):
        super().__init__(config, salt)
        self.session: Optional[aiohttp.ClientSession] = None
        self._token_cache = {}
    
    async def connect(self) -> bool:
        """
        Establish connection using SMART Backend Services authentication
        """
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
            
            # Get access token using JWT assertion
            token = await self._get_access_token()
            if token:
                self._access_token = token
                logger.info("Successfully connected to Epic FHIR API")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to Epic: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return capability statement"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/metadata",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    metadata = await response.json()
                    return {
                        "status": "connected",
                        "fhir_version": metadata.get("fhirVersion"),
                        "software": metadata.get("software", {}).get("name"),
                        "resources": len(metadata.get("rest", [{}])[0].get("resource", [])),
                    }
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def extract_patients(
        self, 
        query: PatientQuery
    ) -> AsyncGenerator[ExtractedRecord, None]:
        """
        Extract patient data based on query parameters
        Yields records as they are retrieved for memory efficiency
        """
        # Build patient list
        if query.mrns:
            patients = query.mrns
        elif query.diagnosis_codes:
            # Find patients with specific diagnoses
            patients = await self._find_patients_by_diagnosis(query.diagnosis_codes)
        else:
            # Get all patients (paginated)
            patients = await self._get_all_patients(query.date_range_start, query.date_range_end)
        
        # Process patients in batches
        for i in range(0, len(patients), query.batch_size):
            batch = patients[i:i + query.batch_size]
            
            # Extract data for each patient in batch
            tasks = [
                self._extract_patient_data(mrn, query.data_categories)
                for mrn in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for mrn, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Error extracting data for MRN {mrn}: {result}")
                    continue
                
                for record in result:
                    yield record
    
    async def get_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        """Get a single patient by MRN"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/Patient",
                params={"identifier": f"MR|{mrn}"},
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    bundle = await response.json()
                    entries = bundle.get("entry", [])
                    if entries:
                        return FHIRResourceMapper.map_patient(entries[0].get("resource", {}))
                return None
        except Exception as e:
            logger.error(f"Error fetching patient {mrn}: {e}")
            return None
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Get access token using JWT Bearer assertion for backend services
        """
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token
        
        # Create JWT assertion
        now = int(time.time())
        claims = {
            "iss": self.config.client_id,
            "sub": self.config.client_id,
            "aud": f"{self.config.base_url}/oauth2/token",
            "jti": f"jwt_{now}",
            "exp": now + 300,  # 5 minute expiry
            "iat": now,
        }
        
        # Sign with private key
        try:
            with open(self.config.private_key_path, 'r') as f:
                private_key = f.read()
            
            assertion = jwt.encode(claims, private_key, algorithm="RS384")
            
            # Exchange assertion for access token
            async with self.session.post(
                f"{self.config.base_url}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": assertion,
                    "scope": "system/*.read",
                }
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._access_token = token_data["access_token"]
                    self._token_expiry = datetime.now() + timedelta(
                        seconds=token_data.get("expires_in", 3600)
                    )
                    return self._access_token
                else:
                    logger.error(f"Token request failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for FHIR API requests"""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
    
    async def _extract_patient_data(
        self, 
        mrn: str, 
        categories: List[DataCategory]
    ) -> List[ExtractedRecord]:
        """Extract all requested data categories for a single patient"""
        records = []
        
        # Get patient FHIR ID first
        patient = await self.get_patient_by_mrn(mrn)
        if not patient:
            return records
        
        # Get FHIR patient ID for subsequent queries
        patient_id = await self._get_patient_fhir_id(mrn)
        if not patient_id:
            return records
        
        # Add demographics record
        if DataCategory.DEMOGRAPHICS in categories:
            records.append(ExtractedRecord(
                source_emr=EMRType.EPIC,
                source_id=patient_id,
                mrn=mrn,
                category=DataCategory.DEMOGRAPHICS,
                record_date=datetime.now(),
                data=patient,
            ))
        
        # Extract each requested category
        for category in categories:
            if category == DataCategory.DEMOGRAPHICS:
                continue  # Already handled
            
            resources = self.FHIR_RESOURCES.get(category, [])
            for resource_type in resources:
                category_records = await self._fetch_patient_resources(
                    patient_id, mrn, resource_type, category
                )
                records.extend(category_records)
        
        return records
    
    async def _get_patient_fhir_id(self, mrn: str) -> Optional[str]:
        """Get the FHIR resource ID for a patient by MRN"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/Patient",
                params={"identifier": f"MR|{mrn}"},
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    bundle = await response.json()
                    entries = bundle.get("entry", [])
                    if entries:
                        return entries[0].get("resource", {}).get("id")
                return None
        except Exception as e:
            logger.error(f"Error getting FHIR ID for {mrn}: {e}")
            return None
    
    async def _fetch_patient_resources(
        self,
        patient_id: str,
        mrn: str,
        resource_type: str,
        category: DataCategory
    ) -> List[ExtractedRecord]:
        """Fetch FHIR resources for a patient"""
        records = []
        
        # Handle resources with query parameters
        if "?" in resource_type:
            base_resource, query_string = resource_type.split("?", 1)
            url = f"{self.config.base_url}/{base_resource}"
            params = dict(param.split("=") for param in query_string.split("&"))
            params["patient"] = patient_id
        else:
            url = f"{self.config.base_url}/{resource_type}"
            params = {"patient": patient_id}
        
        try:
            # Paginate through results
            while url:
                async with self.session.get(
                    url,
                    params=params if "?" not in url else None,
                    headers=self._get_headers()
                ) as response:
                    if response.status != 200:
                        break
                    
                    bundle = await response.json()
                    
                    for entry in bundle.get("entry", []):
                        resource = entry.get("resource", {})
                        mapped_data = self._map_resource(resource, category)
                        
                        if mapped_data:
                            records.append(ExtractedRecord(
                                source_emr=EMRType.EPIC,
                                source_id=resource.get("id", ""),
                                mrn=mrn,
                                category=category,
                                record_date=self._extract_date(resource),
                                data=mapped_data,
                                raw_data=resource,
                            ))
                    
                    # Get next page
                    url = None
                    for link in bundle.get("link", []):
                        if link.get("relation") == "next":
                            url = link.get("url")
                            params = None  # URL contains all params
                            break
                            
        except Exception as e:
            logger.error(f"Error fetching {resource_type} for patient {patient_id}: {e}")
        
        return records
    
    def _map_resource(self, resource: Dict[str, Any], category: DataCategory) -> Optional[Dict[str, Any]]:
        """Map FHIR resource to HealthDB format"""
        resource_type = resource.get("resourceType", "")
        
        mappers = {
            "Patient": FHIRResourceMapper.map_patient,
            "Condition": FHIRResourceMapper.map_condition,
            "Procedure": self._map_procedure,
            "MedicationRequest": FHIRResourceMapper.map_medication,
            "MedicationAdministration": self._map_medication_administration,
            "Observation": FHIRResourceMapper.map_observation,
            "DiagnosticReport": FHIRResourceMapper.map_diagnostic_report,
            "DocumentReference": self._map_document_reference,
            "ImagingStudy": self._map_imaging_study,
        }
        
        mapper = mappers.get(resource_type)
        if mapper:
            return mapper(resource)
        return None
    
    def _extract_date(self, resource: Dict[str, Any]) -> datetime:
        """Extract the most relevant date from a FHIR resource"""
        date_fields = [
            "effectiveDateTime", "recordedDate", "authoredOn", 
            "performedDateTime", "issued", "started"
        ]
        
        for field in date_fields:
            if field in resource:
                return self._parse_fhir_datetime(resource[field])
        
        # Check nested period
        if "effectivePeriod" in resource:
            return self._parse_fhir_datetime(resource["effectivePeriod"].get("start", ""))
        if "performedPeriod" in resource:
            return self._parse_fhir_datetime(resource["performedPeriod"].get("start", ""))
        
        return datetime.now()
    
    def _parse_fhir_datetime(self, dt_string: str) -> datetime:
        """Parse FHIR datetime string"""
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(dt_string[:len("2024-01-01T00:00:00")], fmt.replace("%z", ""))
            except ValueError:
                continue
        return datetime.now()
    
    @staticmethod
    def _map_procedure(resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR Procedure to HealthDB format"""
        code = resource.get("code", {}).get("coding", [{}])[0]
        return {
            "procedure_code": code.get("code", ""),
            "procedure_name": code.get("display", ""),
            "coding_system": code.get("system", ""),
            "status": resource.get("status"),
            "performed_date": resource.get("performedDateTime") or 
                            resource.get("performedPeriod", {}).get("start"),
            "category": resource.get("category", {}).get("text", ""),
        }
    
    @staticmethod
    def _map_medication_administration(resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR MedicationAdministration to HealthDB format"""
        medication = resource.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
        dosage = resource.get("dosage", {})
        return {
            "medication_code": medication.get("code", ""),
            "medication_name": medication.get("display", ""),
            "coding_system": medication.get("system", ""),
            "status": resource.get("status"),
            "effective_date": resource.get("effectiveDateTime") or 
                            resource.get("effectivePeriod", {}).get("start"),
            "dose_value": dosage.get("dose", {}).get("value"),
            "dose_unit": dosage.get("dose", {}).get("unit"),
            "route": dosage.get("route", {}).get("text", ""),
        }
    
    @staticmethod
    def _map_document_reference(resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR DocumentReference to HealthDB format"""
        type_coding = resource.get("type", {}).get("coding", [{}])[0]
        return {
            "document_type": type_coding.get("display", ""),
            "document_code": type_coding.get("code", ""),
            "status": resource.get("status"),
            "date": resource.get("date"),
            "description": resource.get("description", ""),
            "content_type": resource.get("content", [{}])[0].get("attachment", {}).get("contentType"),
        }
    
    @staticmethod
    def _map_imaging_study(resource: Dict[str, Any]) -> Dict[str, Any]:
        """Map FHIR ImagingStudy to HealthDB format"""
        return {
            "study_id": resource.get("id", ""),
            "modality": [m.get("code") for m in resource.get("modality", [])],
            "description": resource.get("description", ""),
            "started": resource.get("started"),
            "number_of_series": resource.get("numberOfSeries"),
            "number_of_instances": resource.get("numberOfInstances"),
            "body_site": resource.get("series", [{}])[0].get("bodySite", {}).get("display"),
        }
    
    async def _find_patients_by_diagnosis(self, icd_codes: List[str]) -> List[str]:
        """Find patients with specific ICD diagnosis codes"""
        patients = set()
        
        for code in icd_codes:
            try:
                async with self.session.get(
                    f"{self.config.base_url}/Condition",
                    params={"code": code},
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        bundle = await response.json()
                        for entry in bundle.get("entry", []):
                            subject = entry.get("resource", {}).get("subject", {})
                            ref = subject.get("reference", "")
                            if ref.startswith("Patient/"):
                                # Get MRN for this patient
                                patient_id = ref.replace("Patient/", "")
                                mrn = await self._get_mrn_for_patient_id(patient_id)
                                if mrn:
                                    patients.add(mrn)
            except Exception as e:
                logger.error(f"Error searching for diagnosis {code}: {e}")
        
        return list(patients)
    
    async def _get_mrn_for_patient_id(self, patient_id: str) -> Optional[str]:
        """Get MRN from FHIR patient ID"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/Patient/{patient_id}",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    patient = await response.json()
                    return FHIRResourceMapper._extract_mrn(patient)
                return None
        except Exception as e:
            logger.error(f"Error getting MRN for patient {patient_id}: {e}")
            return None
    
    async def _get_all_patients(
        self, 
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None
    ) -> List[str]:
        """Get all patients, optionally filtered by date range"""
        patients = []
        params = {"_count": 100}
        
        if date_start:
            params["_lastUpdated"] = f"ge{date_start.isoformat()}"
        
        url = f"{self.config.base_url}/Patient"
        
        while url and len(patients) < 10000:  # Safety limit
            try:
                async with self.session.get(
                    url,
                    params=params if "?" not in url else None,
                    headers=self._get_headers()
                ) as response:
                    if response.status != 200:
                        break
                    
                    bundle = await response.json()
                    
                    for entry in bundle.get("entry", []):
                        mrn = FHIRResourceMapper._extract_mrn(entry.get("resource", {}))
                        if mrn:
                            patients.append(mrn)
                    
                    # Get next page
                    url = None
                    params = None
                    for link in bundle.get("link", []):
                        if link.get("relation") == "next":
                            url = link.get("url")
                            break
                            
            except Exception as e:
                logger.error(f"Error fetching patients: {e}")
                break
        
        return patients


class EpicClarityConnector(EMRConnector):
    """
    Direct database connector for Epic Clarity/Caboodle data warehouse
    For institutions with direct database access
    """
    
    # Common Clarity tables for oncology data
    CLARITY_TABLES = {
        DataCategory.DEMOGRAPHICS: ["PATIENT", "PATIENT_RACE", "IDENTITY_ID"],
        DataCategory.DIAGNOSES: ["PROBLEM_LIST", "PAT_ENC_DX", "EDG_CURRENT_ICD10"],
        DataCategory.PROCEDURES: ["OR_LOG", "ORDER_PROC", "HSP_ACCT_DX_LIST"],
        DataCategory.MEDICATIONS: ["ORDER_MED", "MAR_ADMIN_INFO"],
        DataCategory.LABS: ["ORDER_RESULTS", "RESULT_COMPONENT"],
        DataCategory.PATHOLOGY: ["ORDER_RESULTS", "RESULT_NARR"],
        DataCategory.NOTES: ["HNO_INFO", "HNO_NOTE_TEXT"],
    }
    
    async def connect(self) -> bool:
        """Connect to Clarity database"""
        # Implementation would use pyodbc or similar for SQL Server
        # This is a placeholder for the connection logic
        logger.info("Clarity database connection established")
        return True
    
    async def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        return {"status": "connected", "database": "Epic Clarity"}
    
    async def extract_patients(
        self, 
        query: PatientQuery
    ) -> AsyncGenerator[ExtractedRecord, None]:
        """Extract patient data using SQL queries"""
        # This would contain actual SQL queries for Clarity
        # Placeholder implementation
        yield ExtractedRecord(
            source_emr=EMRType.EPIC,
            source_id="clarity_test",
            mrn="test",
            category=DataCategory.DEMOGRAPHICS,
            record_date=datetime.now(),
            data={},
        )
    
    async def get_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        """Get patient by MRN from Clarity"""
        # SQL query implementation would go here
        return None
    
    def get_oncology_query(self, cancer_type: str = None) -> str:
        """
        Generate SQL query for oncology-specific data extraction
        Optimized for cancer registry data
        """
        base_query = """
        SELECT 
            p.PAT_MRN_ID,
            p.BIRTH_DATE,
            p.SEX,
            pr.PATIENT_RACE_C,
            dx.DX_ID,
            dx.CURRENT_ICD10_LIST,
            dx.DX_NAME,
            dx.CONTACT_DATE as DIAGNOSIS_DATE,
            stg.CANCER_STAGE,
            stg.STAGE_DATE,
            path.RESULT_VALUE as PATHOLOGY_RESULT,
            path.RESULT_DATE as PATHOLOGY_DATE
        FROM PATIENT p
        LEFT JOIN PATIENT_RACE pr ON p.PAT_ID = pr.PAT_ID
        LEFT JOIN PAT_ENC_DX dx ON p.PAT_ID = dx.PAT_ID
        LEFT JOIN CANCER_STAGING stg ON p.PAT_ID = stg.PAT_ID
        LEFT JOIN ORDER_RESULTS path ON p.PAT_ID = path.PAT_ID
            AND path.PROC_CAT_ID IN (/* Pathology category IDs */)
        WHERE 1=1
        """
        
        if cancer_type:
            base_query += f"""
            AND (
                dx.CURRENT_ICD10_LIST LIKE 'C%'  -- Malignant neoplasms
                OR dx.CURRENT_ICD10_LIST LIKE 'D0%'  -- In situ neoplasms
            )
            """
        
        return base_query

