import hashlib
import json
import os
import logging
from presidio_analyzer import AnalyzerEngine  # Microsoft's PHI detection library
from presidio_anonymizer import AnonymizerEngine

logger = logging.getLogger("healthdb.deidentification")


class DeIdentifier:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.salt = self._load_salt_from_vault()

    def hash_patient_id(self, raw_id: str) -> str:
        """Hash patient ID using SHA-256 with salt"""
        salted = f"{raw_id}-{self.salt}".encode()
        return hashlib.sha256(salted).hexdigest()

    def deidentify_data(self, data: dict, disease_template: dict) -> dict:
        """
        Process data through:
        1. PHI detection
        2. Data validation against template
        3. De-identification
        """
        # Validate against disease-specific template
        self._validate_data(data, disease_template)

        # Detect and anonymize PHI - expanded entity list per HIPAA Safe Harbor
        text_data = json.dumps(data)
        analysis_results = self.analyzer.analyze(
            text=text_data,
            language="en",
            entities=["PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER",
                      "EMAIL_ADDRESS", "US_SSN", "MEDICAL_LICENSE",
                      "US_DRIVER_LICENSE", "IP_ADDRESS", "URL"]
        )
        anonymized = self.anonymizer.anonymize(
            text=text_data,
            analyzer_results=analysis_results
        )

        return self._process_anonymized(anonymized.text, disease_template)

    def _validate_data(self, data: dict, template: dict):
        """Validate data against disease template requirements"""
        if not template:
            logger.warning("No disease template provided for validation")
            return

        required_fields = template.get("required_fields", [])
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Validate field types if specified
        field_types = template.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if expected_type == "string" and not isinstance(data[field], str):
                    raise ValueError(f"Field '{field}' must be a string")
                elif expected_type == "number" and not isinstance(data[field], (int, float)):
                    raise ValueError(f"Field '{field}' must be a number")

    def _process_anonymized(self, text: str, template: dict) -> dict:
        """Post-processing to ensure data structure integrity"""
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse anonymized text back to JSON")
            raise ValueError("De-identification produced invalid JSON output")

        # Verify no known PHI patterns remain in output
        phi_check = self.analyzer.analyze(
            text=json.dumps(result), language="en",
            entities=["PERSON", "US_SSN", "PHONE_NUMBER", "EMAIL_ADDRESS"]
        )
        high_confidence_phi = [r for r in phi_check if r.score >= 0.85]
        if high_confidence_phi:
            logger.error(f"PHI still detected in output: {len(high_confidence_phi)} entities")
            raise ValueError("De-identification incomplete: PHI still detected in output")

        return result

    def _load_salt_from_vault(self) -> str:
        """Retrieve salt from secure storage (environment variable or secrets manager)"""
        salt = os.environ.get("DEIDENTIFICATION_SALT")
        if not salt:
            if os.environ.get("ENVIRONMENT", "development") == "production":
                raise RuntimeError(
                    "DEIDENTIFICATION_SALT environment variable must be set in production. "
                    "Use a cryptographically random value from your secrets manager."
                )
            logger.warning("Using development-only deidentification salt")
            salt = "dev-only-salt-not-for-production"
        return salt
