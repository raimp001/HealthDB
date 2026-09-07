"""Tests for the release manifest.

The manifest is only worth having if it detects change. Most of these assert
that altering something produces a different digest, because a hash that
stays the same when the content moves is worse than no hash: it certifies
the wrong file.
"""
import pytest

from api.release_manifest import (
    MANIFEST_SCHEMA_VERSION,
    build_manifest,
    canonical_json,
    digest,
    manifest_digest,
    verify_manifest,
)


BASE = dict(
    job_id="job-1", study_id="study-1", study_name="Study",
    released_to="user-1", released_at="2026-01-01T00:00:00",
    variables=["diagnosis.stage"], subject_count=11, record_count=11,
    content_digest="abc", cohort_criteria={"cancer_type": "breast"},
    disclosure_risk={"min_k": 11, "meets_threshold": True},
    approvals=[{"id": "a1", "document_type": "irb_protocol", "status": "approved"}],
    deidentification_level="limited_dataset",
)


def test_canonical_json_is_insensitive_to_key_order():
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


def test_canonical_json_is_sensitive_to_values():
    assert canonical_json({"a": 1}) != canonical_json({"a": 2})


def test_manifest_verifies_against_its_own_digest():
    manifest = build_manifest(**BASE)
    assert verify_manifest(manifest, manifest_digest(manifest)) is True


@pytest.mark.parametrize("field,value", [
    ("subject_count", 10),
    ("record_count", 12),
    ("content_digest", "def"),
    ("study_id", "study-2"),
    ("released_to", "user-2"),
    ("deidentification_level", "safe_harbor"),
])
def test_changing_any_recorded_fact_breaks_the_digest(field, value):
    manifest = build_manifest(**BASE)
    recorded = manifest_digest(manifest)
    manifest[field] = value
    assert verify_manifest(manifest, recorded) is False


def test_changing_the_risk_report_breaks_the_digest():
    """Nobody may retroactively make a blocked release look compliant."""
    manifest = build_manifest(**BASE)
    recorded = manifest_digest(manifest)
    manifest["disclosure_risk"]["meets_threshold"] = False
    assert verify_manifest(manifest, recorded) is False


def test_removing_an_approval_breaks_the_digest():
    manifest = build_manifest(**BASE)
    recorded = manifest_digest(manifest)
    manifest["approvals"] = []
    assert verify_manifest(manifest, recorded) is False


def test_variable_order_does_not_change_the_release():
    """Selecting the same variables in another order is the same release."""
    a = build_manifest(**{**BASE, "variables": ["b", "a"]})
    b = build_manifest(**{**BASE, "variables": ["a", "b"]})
    assert manifest_digest(a) == manifest_digest(b)


def test_approval_order_does_not_change_the_release():
    approvals = [
        {"id": "a1", "document_type": "irb_protocol", "status": "approved"},
        {"id": "a2", "document_type": "dua", "status": "signed"},
    ]
    a = build_manifest(**{**BASE, "approvals": approvals})
    b = build_manifest(**{**BASE, "approvals": list(reversed(approvals))})
    assert manifest_digest(a) == manifest_digest(b)


def test_a_manifest_from_another_schema_version_does_not_verify():
    """An old manifest must not be re-hashed under new rules and pass."""
    manifest = build_manifest(**BASE)
    recorded = manifest_digest(manifest)
    manifest["schema_version"] = MANIFEST_SCHEMA_VERSION + 1
    assert verify_manifest(manifest, recorded) is False


def test_content_digest_detects_a_one_character_csv_change():
    original = "a,b\n1,2\n"
    altered = "a,b\n1,3\n"
    assert digest(original) != digest(altered)


def test_digest_accepts_str_and_bytes_alike():
    assert digest("x") == digest(b"x")
