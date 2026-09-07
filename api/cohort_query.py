"""One cohort evaluator shared by feasibility, saved cohorts and exports.

Queries use recorded values only. Missing values never establish an inclusion
or a negative finding. Age-band comparisons require the entire recorded band
to satisfy the requested bounds; an overlapping band is not an exact age.

Clinical dates are stored as a year and nothing finer, so every date-based
comparison here is year-granular. A diagnosis-date range matches on whole
calendar years, and a follow-up duration derived from record dates is a lower
bound, never an estimate.
"""
from collections import defaultdict
from datetime import date
import json
import math
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .terminology import same_concept


FIELDS = {
    "diagnosis": ("diagnosis", ("display", "cancer_type", "code", "icd_code", "icd10_code")),
    "stage": ("diagnosis", ("stage",)),
    "treatment": ("treatment", ("medication", "procedure", "regimen", "display", "treatment_type")),
    "line_of_therapy": ("treatment", ("line_of_therapy", "line")),
    "age": ("demographics", ("age", "age_band")),
    "sex": ("demographics", ("sex",)),
    "ecog": (None, ("ecog", "ecog_status")),
    "prior_cart": (None, ("prior_cart",)),
    "prior_transplant": (None, ("prior_transplant",)),
    "cytogenetics": ("molecular", ("cytogenetics", "marker", "gene", "display")),
    "response": ("outcome", ("response", "best_response")),
    "mrd": (None, ("mrd", "mrd_status")),
    "follow_up": (None, ("follow_up_months", "followup_months")),
}
NUMERIC_FIELDS = {"age", "line_of_therapy", "ecog", "follow_up"}


class CohortRule(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    field: str
    operator: str
    value: str = Field(min_length=1, max_length=200)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_rule(self):
        if self.field not in FIELDS:
            raise ValueError(f"Unsupported cohort field: {self.field}")
        allowed = {"=", ">=", "<=", ">", "<", "BETWEEN"} if self.field in NUMERIC_FIELDS else {"IS", "IS NOT", "IN", "INCLUDES", "EXCLUDES"}
        if self.operator not in allowed:
            raise ValueError(f"Unsupported operator for {self.field}: {self.operator}")
        if self.field in NUMERIC_FIELDS:
            bounds = number_range(self.value)
            if bounds is None or (self.operator == "BETWEEN" and bounds[0] == bounds[1]):
                raise ValueError("Enter a number or a range such as 40-69")
        return self


class CohortCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cancer_types: Optional[List[str]] = None
    icd_codes: Optional[List[str]] = None
    stages: Optional[List[str]] = None
    age_min: Optional[int] = Field(default=None, ge=0, le=130)
    age_max: Optional[int] = Field(default=None, ge=0, le=130)
    molecular_markers: Optional[List[str]] = None
    treatment_types: Optional[List[str]] = None
    min_follow_up_months: Optional[int] = Field(default=None, ge=0, le=1560)
    diagnosis_date_start: Optional[date] = None
    diagnosis_date_end: Optional[date] = None
    inclusions: List[CohortRule] = Field(default_factory=list, max_length=50)
    exclusions: List[CohortRule] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.age_min is not None and self.age_max is not None and self.age_min > self.age_max:
            raise ValueError("Minimum age must not exceed maximum age")
        if self.diagnosis_date_start and self.diagnosis_date_end and self.diagnosis_date_start > self.diagnosis_date_end:
            raise ValueError("Start date must not be after end date")
        for values in (self.cancer_types, self.icd_codes, self.stages, self.molecular_markers, self.treatment_types):
            if values and (len(values) > 100 or any(not value.strip() or len(value) > 200 for value in values)):
                raise ValueError("Filters must contain between 1 and 200 characters per value")
        return self


def payload(record):
    value = record.deidentified_data
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return {}
    return value if isinstance(value, dict) else {}


def normalized(value):
    return re.sub(r"\s+", " ", str(value).strip().lower())


def number_range(value):
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?(\+)?(?: months)?", normalized(value))
    if not match:
        return None
    lower = float(match[1])
    upper = math.inf if match[3] else float(match[2] or match[1])
    return (lower, upper) if lower <= upper else None


def values_for(records, field):
    category, keys = FIELDS[field]
    values = []
    for record in records:
        if category and record.data_category != category:
            continue
        data = payload(record)
        for key in keys:
            value = data.get(key)
            if value is not None and value != "":
                values.extend(value if isinstance(value, list) else [value])
    if field == "follow_up" and not values:
        # Clinical dates are stored as a year (Safe Harbor forbids more
        # precision), so an exact month count cannot be derived. Records
        # spanning first..last year are at least (span - 1) whole years apart
        # — December of the first to January of the last — so that lower bound
        # is what gets reported. Estimating the midpoint instead would invent
        # the precision the truncation deliberately destroyed, and would
        # over-include patients at the boundary of a minimum-follow-up filter.
        years = sorted(r.original_year for r in records if r.original_year)
        if len(years) >= 2:
            values.append(max(0, (years[-1] - years[0] - 1) * 12))
    return values


def text_matches(value, wanted, field, contains=False):
    actual, term = normalized(value), normalized(wanted)
    if field == "stage":
        return actual.removeprefix("stage ") == term.removeprefix("stage ")
    if field == "diagnosis":
        # Two sites can write the same disease three ways. If both sides
        # resolve to the same code, that is a match regardless of wording.
        # Terminology never *rejects* a match: an unmapped term falls through
        # to the string comparison below, so adding a code can only widen
        # recall, never silently narrow an existing cohort.
        if same_concept(value, wanted):
            return True
        # A diagnosis preset includes its ICD family, e.g. AML (C92.0).
        code = re.search(r"\(([a-z]\d[\w.]*)\)$", term)
        if code:
            prefix = code[1].removesuffix(".x")
            if actual.startswith(prefix):
                return True
            term = term[:code.start()].strip()
        elif re.fullmatch(r"[a-z]\d[\d.x]*", term):
            return actual.startswith(term.removesuffix(".x"))
    if contains:
        return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", actual) is not None
    return actual == term


def rule_matches(records, rule):
    values = values_for(records, rule.field)
    if not values:
        return False
    if rule.field in NUMERIC_FIELDS:
        target_low, target_high = number_range(rule.value)
        for value in values:
            bounds = number_range(value)
            if not bounds:
                continue
            low, high = bounds
            if {"=": low == high == target_low, ">=": low >= target_low,
                "<=": high <= target_high, ">": low > target_high,
                "<": high < target_low, "BETWEEN": low >= target_low and high <= target_high}[rule.operator]:
                return True
        return False
    terms = [item.strip() for item in rule.value.split(",")] if rule.operator == "IN" else [rule.value]
    match = any(text_matches(value, term, rule.field, rule.operator in {"INCLUDES", "EXCLUDES"}) for value in values for term in terms)
    return not match if rule.operator in {"IS NOT", "EXCLUDES"} else match


def matching_patient_ids(records, criteria):
    grouped = defaultdict(list)
    for record in records:
        grouped[str(record.patient_id)].append(record)
    matched = set()
    for patient_id, patient_records in grouped.items():
        alternatives = [
            ("diagnosis", (criteria.cancer_types or []) + (criteria.icd_codes or [])),
            ("stage", criteria.stages), ("treatment", criteria.treatment_types),
            ("cytogenetics", criteria.molecular_markers),
        ]
        if any(terms and not any(text_matches(value, term, field, field in {"treatment", "cytogenetics"})
                                  for value in values_for(patient_records, field) for term in terms)
               for field, terms in alternatives):
            continue
        numeric = [("age", ">=", criteria.age_min), ("age", "<=", criteria.age_max),
                   ("follow_up", ">=", criteria.min_follow_up_months)]
        if any(value is not None and not rule_matches(patient_records, CohortRule(field=field, operator=operator, value=str(value)))
               for field, operator, value in numeric):
            continue
        if criteria.diagnosis_date_start or criteria.diagnosis_date_end:
            # Only the year is stored, so the comparison is year-granular. A
            # range starting mid-year therefore includes that whole year: the
            # filter cannot be more precise than the data it filters, and a
            # cohort that quietly dropped in-range patients would be worse
            # than one that is openly coarse.
            start_year = criteria.diagnosis_date_start.year if criteria.diagnosis_date_start else None
            end_year = criteria.diagnosis_date_end.year if criteria.diagnosis_date_end else None
            if not any(r.data_category == "diagnosis" and r.original_year
                       and (start_year is None or r.original_year >= start_year)
                       and (end_year is None or r.original_year <= end_year)
                       for r in patient_records):
                continue
        if any(r.enabled and not rule_matches(patient_records, r) for r in criteria.inclusions):
            continue
        if any(r.enabled and rule_matches(patient_records, r) for r in criteria.exclusions):
            continue
        matched.add(patient_id)
    return matched
