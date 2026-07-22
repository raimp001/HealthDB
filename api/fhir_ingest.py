"""Defensive, de-identified extraction from patient-supplied FHIR R4 bundles.

Only the explicitly supported clinical fields are copied from the bundle. Direct
identifiers and raw birth dates are never included in the returned data payloads.
"""

from datetime import date, datetime
import re


_FHIR_DATE_RE = re.compile(
    r"^(?P<year>(?:19|20)\d{2})"
    r"(?:-(?P<month>0[1-9]|1[0-2])"
    r"(?:-(?P<day>0[1-9]|[12]\d|3[01])(?:T.*)?)?)?$"
)
_YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")

_SYSTEM_LABELS = {
    "http://hl7.org/fhir/sid/icd-10-cm": "ICD-10",
    "http://hl7.org/fhir/sid/icd-10": "ICD-10",
    "http://snomed.info/sct": "SNOMED",
    "http://loinc.org": "LOINC",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
}


def _age_band(birth_date_str, ref_date=None) -> str | None:
    """Return a ten-year age band, top-coded at 90, for a FHIR date value."""
    if not isinstance(birth_date_str, str):
        return None

    match = _FHIR_DATE_RE.match(birth_date_str.strip())
    if not match:
        return None

    try:
        year = int(match.group("year"))
        month = int(match.group("month") or 1)
        day = int(match.group("day") or 1)
        birth_date = date(year, month, day)
        if ref_date is None:
            reference = date.today()
        elif isinstance(ref_date, datetime):
            reference = ref_date.date()
        elif isinstance(ref_date, date):
            reference = ref_date
        elif isinstance(ref_date, str):
            ref_match = _FHIR_DATE_RE.match(ref_date.strip())
            if not ref_match:
                return None
            reference = date(
                int(ref_match.group("year")),
                int(ref_match.group("month") or 1),
                int(ref_match.group("day") or 1),
            )
        else:
            return None
    except (TypeError, ValueError):
        return None

    age = reference.year - birth_date.year
    if (reference.month, reference.day) < (birth_date.month, birth_date.day):
        age -= 1
    if age < 0:
        return None
    if age > 89:
        return "90+"
    lower = (age // 10) * 10
    return f"{lower}-{lower + 9}"


def _year(date_str) -> int | None:
    """Extract a four-digit 1900s or 2000s year from a FHIR date value."""
    if not isinstance(date_str, str):
        return None
    match = _YEAR_RE.search(date_str)
    return int(match.group(1)) if match else None


def _coding_text(codeable_concept) -> str | None:
    """Return the best available human label from a CodeableConcept."""
    if not isinstance(codeable_concept, dict):
        return None

    text = codeable_concept.get("text")
    if text not in (None, ""):
        return str(text)

    codings = codeable_concept.get("coding")
    if not isinstance(codings, list):
        return None
    for coding in codings:
        if not isinstance(coding, dict):
            continue
        display = coding.get("display")
        if display not in (None, ""):
            return str(display)
    for coding in codings:
        if not isinstance(coding, dict):
            continue
        code = coding.get("code")
        if code not in (None, ""):
            return str(code)
    return None


def _coding_code(codeable_concept) -> tuple[str | None, str | None]:
    """Return the first coding's code and normalized coding-system label."""
    if not isinstance(codeable_concept, dict):
        return None, None
    codings = codeable_concept.get("coding")
    if not isinstance(codings, list):
        return None, None

    first = next((item for item in codings if isinstance(item, dict)), None)
    if first is None:
        return None, None
    code = first.get("code")
    system = first.get("system")
    normalized_code = str(code) if code not in (None, "") else None
    normalized_system = str(system) if system not in (None, "") else None
    system_label = _SYSTEM_LABELS.get(normalized_system, normalized_system)
    return normalized_code, system_label


def _dict(value):
    """Return a mapping value or an empty mapping for malformed FHIR fields."""
    return value if isinstance(value, dict) else {}


def _first_interpretation(resource):
    interpretations = resource.get("interpretation")
    if not isinstance(interpretations, list) or not interpretations:
        return None
    return _coding_text(interpretations[0])


def _extension_display(resource, extension_name):
    """Extract a display label from a US Core race or ethnicity extension."""
    extensions = resource.get("extension")
    if not isinstance(extensions, list):
        return None

    for extension in extensions:
        if not isinstance(extension, dict):
            continue
        url = extension.get("url")
        if not isinstance(url, str) or extension_name not in url.lower():
            continue

        candidates = [extension]
        nested = extension.get("extension")
        if isinstance(nested, list):
            candidates.extend(item for item in nested if isinstance(item, dict))

        for candidate in candidates:
            value_coding = candidate.get("valueCoding")
            if isinstance(value_coding, dict):
                display = value_coding.get("display")
                if display not in (None, ""):
                    return str(display)
    return None


def _record(data_category, data_type, original_date, data):
    return {
        "data_category": data_category,
        "data_type": data_type,
        "original_date": original_date if isinstance(original_date, str) else None,
        "data": data,
    }


def parse_fhir_bundle(bundle: dict, ref_date=None) -> list[dict]:
    """Parse supported FHIR R4 resources into minimal clinical record dicts.

    Malformed entries and unsupported resource types are skipped. Returned
    ``data`` mappings contain no direct demographic identifiers or full dates;
    raw dates are exposed only as ``original_date`` for the caller's Date column.
    """
    if not isinstance(bundle, dict):
        return []
    entries = bundle.get("entry")
    if not isinstance(entries, list):
        return []

    patients = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        resource = entry.get("resource")
        if not isinstance(resource, dict) or resource.get("resourceType") != "Patient":
            continue
        patient_id = resource.get("id")
        if isinstance(patient_id, str):
            patients[patient_id] = resource

    records = []
    for entry in entries:
        try:
            if not isinstance(entry, dict):
                continue
            resource = entry.get("resource")
            if not isinstance(resource, dict):
                continue
            resource_type = resource.get("resourceType")

            if resource_type == "Patient":
                data = {
                    "age_band": _age_band(resource.get("birthDate"), ref_date),
                    "sex": resource.get("gender"),
                    "race": _extension_display(resource, "us-core-race"),
                    "ethnicity": _extension_display(resource, "us-core-ethnicity"),
                    "deceased": bool(resource.get("deceasedBoolean"))
                    if resource.get("deceasedBoolean")
                    else None,
                }
                records.append(_record("demographics", "patient", None, data))

                # Vital status as a de-identified outcome (death year only, never
                # a full death date). Emitted only when the bundle states it.
                deceased_datetime = resource.get("deceasedDateTime")
                if isinstance(deceased_datetime, str) and deceased_datetime.strip():
                    records.append(_record("outcome", "vital_status", deceased_datetime, {
                        "vital_status": "Deceased",
                        "death_year": _year(deceased_datetime),
                    }))
                elif resource.get("deceasedBoolean") is True:
                    records.append(_record("outcome", "vital_status", None, {
                        "vital_status": "Deceased",
                        "death_year": None,
                    }))
                elif resource.get("deceasedBoolean") is False:
                    records.append(_record("outcome", "vital_status", None, {
                        "vital_status": "Alive",
                        "death_year": None,
                    }))

            elif resource_type == "Condition":
                code_concept = resource.get("code")
                code, code_system = _coding_code(code_concept)
                onset_period = _dict(resource.get("onsetPeriod"))
                onset = (
                    resource.get("onsetDateTime")
                    or onset_period.get("start")
                    or resource.get("recordedDate")
                )
                data = {
                    "code": code,
                    "code_system": code_system,
                    "display": _coding_text(code_concept),
                    "clinical_status": _coding_text(resource.get("clinicalStatus")),
                    "diagnosis_year": _year(onset),
                }
                records.append(_record("diagnosis", "condition", onset, data))

            elif resource_type == "Observation":
                code_concept = resource.get("code")
                code, code_system = _coding_code(code_concept)
                effective_period = _dict(resource.get("effectivePeriod"))
                effective = (
                    resource.get("effectiveDateTime")
                    or effective_period.get("start")
                    or resource.get("issued")
                )
                value_quantity = _dict(resource.get("valueQuantity"))
                data_type = _coding_text(code_concept) or "observation"
                data = {
                    "code": code,
                    "code_system": code_system,
                    "test": _coding_text(code_concept),
                    "value": value_quantity.get("value"),
                    "unit": value_quantity.get("unit"),
                    "value_string": resource.get("valueString"),
                    "interpretation": _first_interpretation(resource),
                    "year": _year(effective),
                }
                records.append(_record("lab_results", data_type, effective, data))

            elif resource_type in ("MedicationRequest", "MedicationStatement"):
                medication = resource.get("medicationCodeableConcept")
                code, code_system = _coding_code(medication)
                effective_period = _dict(resource.get("effectivePeriod"))
                start = (
                    resource.get("authoredOn")
                    or resource.get("effectiveDateTime")
                    or effective_period.get("start")
                )
                data = {
                    "medication": _coding_text(medication),
                    "code": code,
                    "code_system": code_system,
                    "status": resource.get("status"),
                    "start_year": _year(start),
                }
                records.append(_record("treatment", "medication", start, data))

            elif resource_type == "Procedure":
                code_concept = resource.get("code")
                code, code_system = _coding_code(code_concept)
                performed_period = _dict(resource.get("performedPeriod"))
                performed = (
                    resource.get("performedDateTime")
                    or performed_period.get("start")
                )
                data = {
                    "procedure": _coding_text(code_concept),
                    "code": code,
                    "code_system": code_system,
                    "status": resource.get("status"),
                    "year": _year(performed),
                }
                records.append(_record("treatment", "procedure", performed, data))
        except Exception:
            continue

    return records
