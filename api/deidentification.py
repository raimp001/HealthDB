"""HIPAA Safe Harbor-oriented de-identification helpers.

This module removes direct-identifier fields and redacts common identifier
formats from free text using only the Python standard library. It does not
perform named-entity recognition, so names embedded only in free text may not
be detected; name-bearing keys and the documented regular-expression patterns
are the intended scope.
"""

import re
from typing import Any


IDENTIFIER_KEY_TERMS = (
    "name",
    "email",
    "phone",
    "fax",
    "address",
    "street",
    "city",
    "zip",
    "postal",
    "ssn",
    "social_security",
    "mrn",
    "medical_record",
    "record_number",
    "account",
    "license",
    "certificate",
    "vehicle",
    "device_id",
    "serial",
    "url",
    "ip_address",
    "biometric",
    "fingerprint",
    "face_photo",
    "dob",
    "date_of_birth",
    "birth",
    "death_date",
    "admission_date",
    "discharge_date",
    "contact",
    "guardian",
    "next_of_kin",
    "beneficiary",
)

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
LONG_DIGIT_RE = re.compile(r"\b\d{7,}\b")
# Alphanumeric identifier codes (e.g. MRN "A1234567", "1234567X") -- a short
# letter run adjacent to 5+ digits. Tuned to avoid ICD codes (C83.3) and
# variant notations (R175H), which carry fewer than five consecutive digits.
IDCODE_RE = re.compile(r"\b(?:[A-Za-z]{1,4}\d{5,}|\d{5,}[A-Za-z]{1,4})\b")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")

_MONTH_NAMES = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?"
)
FULL_DATE_RE = re.compile(
    rf"\b(?:"
    rf"(?:19\d{{2}}|20\d{{2}})-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])"
    rf"|(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:\d{{2}}|19\d{{2}}|20\d{{2}})"
    rf"|(?:{_MONTH_NAMES})\s+(?:0?[1-9]|[12]\d|3[01])(?:,)?\s+(?:\d{{2}}|19\d{{2}}|20\d{{2}})"
    rf")\b",
    re.IGNORECASE,
)

_FOUR_DIGIT_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_AGE_NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
# "age" as a whole word within a key, so top-coding applies to age fields
# ("age", "age_range", "patient_age") but not to "stage", "dosage",
# "coverage", "average", etc.
_AGE_KEY_RE = re.compile(r"(?:^|[_\s-])age(?:$|[_\s-])")

# Keys that match an identifier term ("name") only because they name a
# clinical entity, not a person. Retained so research utility survives; their
# string values are still redacted like any other value.
CLINICAL_NAME_ALLOWLIST = frozenset({
    "gene_name", "drug_name", "medication_name", "med_name", "regimen_name",
    "test_name", "protocol_name", "biomarker_name", "variant_name",
    "disease_name", "marker_name", "therapy_name", "procedure_name",
    "lab_name", "panel_name", "assay_name", "study_name", "trial_name",
})

# Safe structured fields that happen to contain an identifier term as a
# substring ("ethnicity" contains "city").
SAFE_KEY_ALLOWLIST = CLINICAL_NAME_ALLOWLIST | frozenset({"ethnicity"})


def _is_identifier_key(key: Any) -> bool:
    """Return whether a structured key denotes a direct identifier."""
    lowered_key = str(key).lower()
    return (
        lowered_key not in SAFE_KEY_ALLOWLIST
        and any(term in lowered_key for term in IDENTIFIER_KEY_TERMS)
    )


def _replace_full_date(match: re.Match[str]) -> str:
    """Reduce a full date to its four-digit year, when one is present."""
    year = _FOUR_DIGIT_YEAR_RE.search(match.group(0))
    return year.group(0) if year else "[REDACTED-DATE]"


def redact_text(text: str) -> str:
    """Redact common direct-identifier formats from a string value."""
    scrubbed = EMAIL_RE.sub("[REDACTED]", text)
    scrubbed = URL_RE.sub("[REDACTED]", scrubbed)
    scrubbed = FULL_DATE_RE.sub(_replace_full_date, scrubbed)
    scrubbed = SSN_RE.sub("[REDACTED]", scrubbed)
    scrubbed = IDCODE_RE.sub("[REDACTED]", scrubbed)
    scrubbed = ZIP_RE.sub("[REDACTED]", scrubbed)
    scrubbed = PHONE_RE.sub("[REDACTED]", scrubbed)
    scrubbed = LONG_DIGIT_RE.sub("[REDACTED]", scrubbed)
    scrubbed = IPV4_RE.sub("[REDACTED]", scrubbed)
    return scrubbed


# Clinical terminology systems whose numeric concept identifiers (e.g. SNOMED
# CT and RxNorm codes are long digit runs) are legitimate research data, not
# personal identifiers. A "code" value is exempted from numeric-identifier
# redaction only when its sibling "code_system" names one of these, so an
# arbitrary number smuggled into a code field without a recognized system is
# still treated as a potential identifier.
RECOGNIZED_CODE_SYSTEMS = frozenset({"ICD-10", "SNOMED", "LOINC", "RxNorm"})
CODE_VALUE_KEYS = frozenset({"code"})

# The numeric-identifier patterns that collide with clinical concept codes;
# skipped for recognized code values, while contact/date identifiers are not.
_NUMERIC_ID_PATTERNS = (IDCODE_RE, ZIP_RE, LONG_DIGIT_RE)


def _redact_code_value(text: str) -> str:
    """Redact contact/date identifiers from a code value but preserve the
    numeric concept identifier itself (SNOMED/RxNorm codes are digit runs)."""
    scrubbed = EMAIL_RE.sub("[REDACTED]", text)
    scrubbed = URL_RE.sub("[REDACTED]", scrubbed)
    scrubbed = FULL_DATE_RE.sub(_replace_full_date, scrubbed)
    scrubbed = SSN_RE.sub("[REDACTED]", scrubbed)
    scrubbed = PHONE_RE.sub("[REDACTED]", scrubbed)
    scrubbed = IPV4_RE.sub("[REDACTED]", scrubbed)
    return scrubbed


def _has_recognized_code_system(mapping) -> bool:
    """True if a dict carries a code_system naming a known terminology."""
    if not isinstance(mapping, dict):
        return False
    return str(mapping.get("code_system", "")).strip() in RECOGNIZED_CODE_SYSTEMS


def _cap_age(value: Any) -> Any:
    """Apply Safe Harbor's top-coding rule to ages over 89."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "90+" if value > 89 else value
    if isinstance(value, str):
        for match in _AGE_NUMBER_RE.finditer(value):
            if float(match.group(0)) > 89:
                return "90+"
    return value


def deidentify_value(value: Any) -> Any:
    """Recursively remove identifier fields and redact string values."""
    if isinstance(value, dict):
        preserve_code = _has_recognized_code_system(value)
        scrubbed = {}
        for key, item in value.items():
            lowered_key = str(key).lower()
            if _is_identifier_key(key):
                continue
            if preserve_code and lowered_key in CODE_VALUE_KEYS and isinstance(item, str):
                scrubbed[key] = _redact_code_value(item)
                continue
            if _AGE_KEY_RE.search(lowered_key):
                item = _cap_age(item)
            scrubbed[key] = deidentify_value(item)
        return scrubbed
    if isinstance(value, list):
        return [deidentify_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def deidentify_record(data: Any) -> Any:
    """Return a recursively de-identified copy of a record or collection."""
    return deidentify_value(data)


def find_residual_identifiers(value: Any) -> list[str]:
    """Conservatively describe potential identifiers remaining in a value."""
    findings: list[str] = []

    contact_date_checks = (
        ("email", EMAIL_RE),
        ("phone", PHONE_RE),
        ("ssn", SSN_RE),
        ("full date", FULL_DATE_RE),
        ("url", URL_RE),
        ("ip address", IPV4_RE),
    )
    numeric_id_checks = (
        ("id code", IDCODE_RE),
        ("long digit run", LONG_DIGIT_RE),
        ("zip code", ZIP_RE),
    )

    def scan(item: Any, exempt_numeric: bool = False) -> None:
        if isinstance(item, dict):
            preserve_code = _has_recognized_code_system(item)
            for key, nested in item.items():
                if _is_identifier_key(key):
                    findings.append(f"identifier key: {key}")
                child_exempt = preserve_code and str(key).lower() in CODE_VALUE_KEYS
                scan(nested, exempt_numeric=child_exempt)
            return
        if isinstance(item, list):
            for nested in item:
                scan(nested)
            return
        if not isinstance(item, str):
            return

        checks = contact_date_checks if exempt_numeric else contact_date_checks + numeric_id_checks
        for identifier_type, pattern in checks:
            if pattern.search(item):
                findings.append(f"residual {identifier_type} in value")

    scan(value)
    return findings
