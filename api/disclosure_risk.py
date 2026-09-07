"""Re-identification risk measurement for research exports.

The de-identification module removes direct identifiers. That is necessary
but not sufficient: a row with no name, no MRN and no full date can still be
unique on its combination of *quasi-identifiers* — year, age band, sex,
geography, rare diagnosis — and a unique row is a re-identifiable row when an
adversary holds an external dataset with the same attributes.

This module measures that residual risk so it can be acted on before release,
and so a reviewer has numbers rather than assurances.

WHAT THIS IS NOT
----------------
k-anonymity is a measurable property, not a compliance determination. Meeting
a k threshold does not make an export HIPAA de-identified under either Safe
Harbor or Expert Determination. Only a qualified statistician can make that
call, and none has reviewed this pipeline. These figures are the input to that
review, not a substitute for it.

Known limits, stated so a reviewer does not have to discover them:

* k-anonymity does not protect against attribute disclosure. Every record in
  an equivalence class can share the same sensitive value, so membership in
  the class reveals it. l-diversity is reported alongside k for that reason.
* The quasi-identifier set is a judgement call. Anything an adversary might
  join on is a quasi-identifier; this module measures the fields it is told
  about and cannot know what external data exists.
* Repeated queries against overlapping cohorts can defeat a per-export
  threshold. Nothing here tracks disclosure across releases.
* An export with several rows per subject must be measured per subject, not
  per row: an adversary reading the file sees every row that shares a
  pseudonym, so the linkable unit is the subject's whole attribute set. Pass
  ``collapse_by_subject=True`` for that. Measuring per row on such an export
  reports a larger k than the release actually offers.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

# Fields treated as quasi-identifiers by default. Deliberately broad: an
# attribute is a quasi-identifier if an adversary could plausibly know it from
# another source, not only if it looks identifying on its own.
DEFAULT_QUASI_IDENTIFIERS = (
    "original_year",
    "year",
    "age",
    "age_band",
    "age_range",
    "sex",
    "gender",
    "race",
    "ethnicity",
    "zip",
    "zip3",
    "postal_code",
    "state",
    "cancer_type",
    "primary_site",
    "stage",
    "histology",
    "vital_status",
)

# Attributes whose disclosure is the harm, used for l-diversity.
DEFAULT_SENSITIVE_ATTRIBUTES = (
    "cancer_type",
    "primary_site",
    "stage",
    "histology",
    "vital_status",
    "diagnosis",
)


@dataclass
class RiskReport:
    """Measured disclosure risk for one export."""

    record_count: int
    subject_count: int
    quasi_identifiers: Sequence[str]
    min_k: int
    min_l: int
    threshold_k: int
    unique_classes: int
    small_classes: int
    at_risk_records: int
    class_size_histogram: Mapping[int, int] = field(default_factory=dict)
    unit: str = "record"

    @property
    def meets_threshold(self) -> bool:
        """True when every equivalence class is at least `threshold_k` in size.

        An empty export trivially meets it: there is nothing to disclose.
        """
        return self.record_count == 0 or self.min_k >= self.threshold_k

    def summary(self) -> str:
        if self.record_count == 0:
            return "Empty export: nothing to disclose."
        verdict = "meets" if self.meets_threshold else "DOES NOT MEET"
        return (
            f"{self.record_count} records across {self.subject_count} subjects, "
            f"measured per {self.unit}. "
            f"Smallest equivalence class k={self.min_k} (threshold {self.threshold_k}); "
            f"l={self.min_l}. {self.unique_classes} unique combination(s), "
            f"{self.at_risk_records} {self.unit}(s) below threshold. "
            f"Export {verdict} the configured threshold. "
            "This is a measurement, not a de-identification determination."
        )

    def as_dict(self) -> dict:
        return {
            "record_count": self.record_count,
            "subject_count": self.subject_count,
            "quasi_identifiers": list(self.quasi_identifiers),
            "min_k": self.min_k,
            "min_l": self.min_l,
            "threshold_k": self.threshold_k,
            "unique_classes": self.unique_classes,
            "small_classes": self.small_classes,
            "at_risk_records": self.at_risk_records,
            "class_size_histogram": dict(self.class_size_histogram),
            "unit": self.unit,
            "meets_threshold": self.meets_threshold,
            "caveat": (
                "k-anonymity is a measurement, not a compliance determination. "
                "No qualified statistician has reviewed this pipeline."
            ),
        }


def _flatten(value: Any, prefix: str = "", out: dict | None = None) -> dict:
    """Collect scalar leaves from a nested record, keyed by their field name.

    Quasi-identifiers are matched on the leaf key, so nesting does not hide an
    attribute from the measurement.
    """
    if out is None:
        out = {}
    if isinstance(value, Mapping):
        for key, item in value.items():
            _flatten(item, str(key), out)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _flatten(item, prefix, out)
    elif prefix and isinstance(value, (str, int, float, bool)):
        # Keep the first non-empty value for a repeated key; a record carrying
        # two different values for the same attribute is measured on the first,
        # which is the conservative choice for class sizing.
        out.setdefault(prefix.lower(), value)
    return out


def extract_quasi_identifiers(
    record: Mapping[str, Any],
    fields: Sequence[str] = DEFAULT_QUASI_IDENTIFIERS,
) -> tuple:
    """The quasi-identifier signature of one record.

    Records sharing a signature form an equivalence class. A missing attribute
    is represented distinctly from an empty one, because "unknown" and "blank"
    partition subjects differently.
    """
    flat = _flatten(record)
    return tuple((f, flat.get(f, None)) for f in fields)


def _merge_signatures(signatures: Sequence[tuple]) -> tuple:
    """Combine one subject's per-record signatures into a single signature.

    Each field carries the sorted set of values the subject shows for it, so a
    subject with two years of records is matched only against other subjects
    showing that same pair. This is what an adversary reading the export sees:
    all rows sharing a pseudonym belong to one person.
    """
    merged = defaultdict(set)
    for signature in signatures:
        for field_name, value in signature:
            merged[field_name].add(value)
    return tuple(
        (field_name, tuple(sorted(values, key=lambda v: (v is None, str(v)))))
        for field_name, values in sorted(merged.items())
    )


def assess_records(
    records: Iterable[Mapping[str, Any]],
    *,
    threshold_k: int,
    quasi_identifiers: Sequence[str] = DEFAULT_QUASI_IDENTIFIERS,
    sensitive_attributes: Sequence[str] = DEFAULT_SENSITIVE_ATTRIBUTES,
    subject_key: str = "subject_id",
    collapse_by_subject: bool = False,
) -> RiskReport:
    """Measure k-anonymity and l-diversity over a set of de-identified records.

    With ``collapse_by_subject`` the equivalence classes count subjects rather
    than rows, which is the correct unit whenever one subject contributes more
    than one row to the same file.
    """
    records = list(records)
    unit = "subject" if collapse_by_subject else "record"

    subjects = set()
    flattened = []
    for record in records:
        flat = _flatten(record)
        flattened.append(flat)
        subject = flat.get(subject_key.lower())
        if subject is not None:
            subjects.add(subject)

    if not records:
        return RiskReport(
            record_count=0, subject_count=0, quasi_identifiers=quasi_identifiers,
            min_k=0, min_l=0, threshold_k=threshold_k, unique_classes=0,
            small_classes=0, at_risk_records=0, class_size_histogram={},
            unit=unit,
        )

    # Group into equivalence classes. Each class maps to the flattened records
    # that formed it, so l-diversity can be measured over the same grouping.
    classes: dict[tuple, list] = defaultdict(list)

    if collapse_by_subject:
        by_subject: dict[Any, list] = defaultdict(list)
        for record, flat in zip(records, flattened):
            # A row with no subject key cannot be attributed, so it is treated
            # as its own subject rather than silently merged with others.
            key = flat.get(subject_key.lower(), ("__unattributed__", id(record)))
            by_subject[key].append(flat)
        for key, member_flats in by_subject.items():
            signature = _merge_signatures([
                tuple((f, flat.get(f, None)) for f in quasi_identifiers)
                for flat in member_flats
            ])
            classes[signature].append(member_flats)
    else:
        for flat in flattened:
            signature = tuple((f, flat.get(f, None)) for f in quasi_identifiers)
            classes[signature].append([flat])

    sizes = [len(members) for members in classes.values()]
    min_k = min(sizes)

    # l-diversity: distinct sensitive values within a class. A class of 10 that
    # shares one diagnosis discloses that diagnosis to anyone who can place a
    # subject in it, so a large k with l=1 is not protection.
    min_l = None
    for members in classes.values():
        distinct = set()
        for member in members:
            for flat in member:
                for attribute in sensitive_attributes:
                    if attribute in flat:
                        distinct.add((attribute, flat[attribute]))
        diversity = len(distinct) if distinct else 1
        min_l = diversity if min_l is None else min(min_l, diversity)

    return RiskReport(
        record_count=len(records),
        subject_count=len(subjects),
        quasi_identifiers=quasi_identifiers,
        min_k=min_k,
        min_l=min_l or 0,
        threshold_k=threshold_k,
        unique_classes=sum(1 for s in sizes if s == 1),
        small_classes=sum(1 for s in sizes if s < threshold_k),
        at_risk_records=sum(s for s in sizes if s < threshold_k),
        class_size_histogram=dict(Counter(sizes)),
        unit=unit,
    )
