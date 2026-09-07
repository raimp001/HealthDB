"""Tests for the re-identification risk measurement.

These check that the numbers mean what the report says they mean. A risk
measurement that is wrong in the safe-looking direction is worse than none,
so several of these deliberately assert that risky inputs are reported as
risky rather than merely that safe inputs pass.
"""
import pytest

from api.disclosure_risk import (
    DEFAULT_QUASI_IDENTIFIERS,
    RiskReport,
    assess_records,
    extract_quasi_identifiers,
)


def make(n, **attributes):
    return [dict(attributes, subject_id=f"S{i}") for i in range(n)]


def test_empty_export_has_nothing_to_disclose():
    report = assess_records([], threshold_k=11)
    assert report.record_count == 0
    assert report.meets_threshold is True
    assert "nothing to disclose" in report.summary()


def test_identical_records_form_one_large_class():
    report = assess_records(make(20, year=2020, sex="female"), threshold_k=11)
    assert report.min_k == 20
    assert report.unique_classes == 0
    assert report.meets_threshold is True


def test_a_single_unique_row_fails_the_threshold():
    records = make(20, year=2020, sex="female")
    records.append({"subject_id": "rare", "year": 1931, "sex": "female"})
    report = assess_records(records, threshold_k=11)
    assert report.min_k == 1
    assert report.unique_classes == 1
    assert report.at_risk_records == 1
    assert report.meets_threshold is False
    assert "DOES NOT MEET" in report.summary()


def test_at_risk_count_covers_every_undersized_class_not_just_the_smallest():
    records = (
        make(20, year=2020) + [{"subject_id": f"a{i}", "year": 1999} for i in range(3)]
        + [{"subject_id": f"b{i}", "year": 1998} for i in range(4)]
    )
    report = assess_records(records, threshold_k=11)
    assert report.min_k == 3
    assert report.small_classes == 2
    assert report.at_risk_records == 7


def test_nested_values_are_not_hidden_from_the_measurement():
    """A quasi-identifier buried in a nested payload still forms the class."""
    flat = {"subject_id": "a", "year": 2020}
    nested = {"subject_id": "b", "payload": {"demographics": {"year": 2020}}}
    report = assess_records([flat, nested], threshold_k=2)
    assert report.min_k == 2, "nested year should join the same equivalence class"


def test_missing_attribute_is_distinct_from_a_blank_one():
    records = [
        {"subject_id": "a", "year": 2020, "sex": "female"},
        {"subject_id": "b", "year": 2020, "sex": ""},
        {"subject_id": "c", "year": 2020},
    ]
    report = assess_records(records, threshold_k=2)
    assert report.min_k == 1
    assert report.unique_classes == 3


def test_l_diversity_flags_a_class_that_shares_one_sensitive_value():
    """A large k with l=1 leaks the diagnosis to anyone who locates the class."""
    records = make(30, year=2020, cancer_type="pancreatic")
    report = assess_records(
        records,
        threshold_k=11,
        quasi_identifiers=("year",),
        sensitive_attributes=("cancer_type",),
    )
    assert report.min_k == 30
    assert report.min_l == 1


def test_l_diversity_rises_with_distinct_sensitive_values():
    records = [
        {"subject_id": f"S{i}", "year": 2020, "cancer_type": t}
        for i, t in enumerate(["breast", "lung", "colon"] * 10)
    ]
    report = assess_records(
        records,
        threshold_k=11,
        quasi_identifiers=("year",),
        sensitive_attributes=("cancer_type",),
    )
    assert report.min_l == 3


def test_per_row_measurement_overstates_k_when_subjects_repeat():
    """One subject with eleven rows is not eleven people.

    This is the failure mode collapse_by_subject exists to prevent: measured
    per row the export looks like it clears k=11, measured per subject it is
    a single re-identifiable person.
    """
    records = [{"subject_id": "only-one", "year": 2020} for _ in range(11)]

    per_row = assess_records(records, threshold_k=11)
    assert per_row.min_k == 11
    assert per_row.meets_threshold is True

    per_subject = assess_records(records, threshold_k=11, collapse_by_subject=True)
    assert per_subject.min_k == 1
    assert per_subject.meets_threshold is False
    assert per_subject.unit == "subject"


def test_collapsed_subject_signature_spans_all_of_that_subjects_rows():
    """Two subjects match only if their whole attribute sets match."""
    same = [
        {"subject_id": "a", "year": 2019},
        {"subject_id": "a", "year": 2020},
        {"subject_id": "b", "year": 2019},
        {"subject_id": "b", "year": 2020},
    ]
    assert assess_records(same, threshold_k=2, collapse_by_subject=True).min_k == 2

    differing = [
        {"subject_id": "a", "year": 2019},
        {"subject_id": "a", "year": 2020},
        {"subject_id": "b", "year": 2019},
        {"subject_id": "b", "year": 2021},
    ]
    report = assess_records(differing, threshold_k=2, collapse_by_subject=True)
    assert report.min_k == 1, "different year sets must not share a class"


def test_rows_without_a_subject_key_are_not_merged_together():
    """Unattributed rows must not collapse into one artificially large class."""
    records = [{"year": 2020}, {"year": 2020}]
    report = assess_records(records, threshold_k=2, collapse_by_subject=True)
    assert report.subject_count == 0
    assert report.min_k == 2
    # Each row is its own subject, so the class holds two subjects, not one.
    assert sum(report.class_size_histogram.values()) == 1


def test_subject_count_is_distinct_subjects_not_rows():
    records = [
        {"subject_id": "a", "year": 2020},
        {"subject_id": "a", "year": 2021},
        {"subject_id": "b", "year": 2020},
    ]
    report = assess_records(records, threshold_k=2)
    assert report.record_count == 3
    assert report.subject_count == 2


def test_histogram_accounts_for_every_class():
    records = make(5, year=2020) + make(2, year=1990)
    report = assess_records(records, threshold_k=11)
    assert sum(size * count for size, count in report.class_size_histogram.items()) == 7


def test_report_dict_carries_the_caveat_and_is_json_safe():
    import json

    report = assess_records(make(3, year=2020), threshold_k=11)
    payload = report.as_dict()
    assert payload["meets_threshold"] is False
    assert "not a compliance determination" in payload["caveat"]
    json.dumps(payload)


def test_default_quasi_identifiers_cover_the_exported_year_field():
    """The export writes original_year; it must be treated as identifying."""
    assert "original_year" in DEFAULT_QUASI_IDENTIFIERS


def test_extract_quasi_identifiers_returns_one_entry_per_field():
    signature = extract_quasi_identifiers({"year": 2020}, ("year", "sex"))
    assert signature == (("year", 2020), ("sex", None))
