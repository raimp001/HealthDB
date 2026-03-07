"""
Security configuration for HealthDB
PHI detection rules and de-identification methods per HIPAA Safe Harbor
"""

# HIPAA Safe Harbor - 18 identifiers that must be removed
PHI_DETECTION_RULES = {
    "entities": [
        "PERSON", "DATE_TIME", "LOCATION", "PHONE_NUMBER",
        "EMAIL_ADDRESS", "US_SSN", "MEDICAL_LICENSE",
        "US_DRIVER_LICENSE", "IP_ADDRESS", "URL",
    ],
    "threshold": 0.85,  # Confidence threshold for PHI detection
    "context": ["patient", "medical", "diagnosis", "treatment", "prescription"],
    "safe_harbor_identifiers": [
        "names", "geographic_data", "dates", "phone_numbers",
        "fax_numbers", "email_addresses", "ssn", "mrn",
        "health_plan_beneficiary", "account_numbers",
        "certificate_numbers", "vehicle_identifiers",
        "device_identifiers", "web_urls", "ip_addresses",
        "biometric_identifiers", "photographs", "other_unique_identifiers",
    ],
}

DEIDENTIFICATION_METHODS = {
    "PERSON": "replace",
    "DATE_TIME": "shift",       # Date-shift to preserve temporal relationships
    "LOCATION": "generalize",   # Generalize to 3-digit zip
    "PHONE_NUMBER": "replace",
    "EMAIL_ADDRESS": "replace",
    "US_SSN": "replace",
    "MEDICAL_LICENSE": "replace",
    "US_DRIVER_LICENSE": "replace",
    "IP_ADDRESS": "replace",
    "URL": "replace",
}

# Password policy
PASSWORD_POLICY = {
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "max_age_days": 90,
    "history_count": 12,  # Cannot reuse last 12 passwords
}

# Session security
SESSION_CONFIG = {
    "max_idle_minutes": 15,      # Auto-logout after 15 min idle (HIPAA)
    "max_session_hours": 4,      # Max session duration
    "concurrent_sessions": 1,    # One session per user
}

# Rate limiting (application-level, in addition to nginx)
RATE_LIMITS = {
    "auth_login": "5/minute",
    "auth_register": "3/minute",
    "api_general": "100/minute",
    "data_export": "10/hour",
}
