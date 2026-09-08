"""Where a record came from, recorded without pointing back at a person.

The obvious implementation of provenance is the dangerous one. Storing the
source system's record identifier — a FHIR resource id, an MRN, an encounter
number — hands anyone holding that system a key to match a released row back
to the patient it came from. Most of these tests exist to hold that line.
"""
import json

import pytest

from api import provenance


@pytest.fixture(autouse=True)
def salt(monkeypatch):
    monkeypatch.setenv("PROVENANCE_SALT", "test-salt-for-provenance-digests")


RESOURCE = {
    "resourceType": "Condition",
    "id": "hospital-record-99887766",
    "subject": {"reference": "Patient/mrn-12345"},
    "code": {"text": "Acute myeloid leukemia"},
}


# ---------------------------------------------------------------------------
# It must not carry a way back to the person
# ---------------------------------------------------------------------------

def test_no_source_identifier_survives_into_provenance():
    """The whole point. A resource id is a linkage key, not metadata."""
    record = provenance.build(source_system="synthetic_fhir_bundle",
                              resource_type="Condition", raw=RESOURCE)
    serialized = json.dumps(record)
    assert "hospital-record-99887766" not in serialized
    assert "mrn-12345" not in serialized
    assert "Patient/" not in serialized


def test_the_digest_is_salted_so_it_cannot_confirm_a_candidate(monkeypatch):
    """An unsalted hash would be an oracle: hash a record, test for a match."""
    first = provenance.source_digest(RESOURCE)
    monkeypatch.setenv("PROVENANCE_SALT", "a-different-server-secret")
    assert provenance.source_digest(RESOURCE) != first


def test_the_same_resource_digests_the_same_way():
    """Which is the property that makes duplicate detection possible."""
    assert provenance.source_digest(RESOURCE) == provenance.source_digest(dict(RESOURCE))


def test_key_order_does_not_change_the_digest():
    reordered = {k: RESOURCE[k] for k in reversed(list(RESOURCE))}
    assert provenance.source_digest(reordered) == provenance.source_digest(RESOURCE)


def test_a_changed_resource_digests_differently():
    altered = dict(RESOURCE, code={"text": "Chronic myeloid leukemia"})
    assert provenance.source_digest(altered) != provenance.source_digest(RESOURCE)


# ---------------------------------------------------------------------------
# It must not become a field a caller can write prose into
# ---------------------------------------------------------------------------

def test_an_unrecognised_source_system_is_recorded_as_unknown():
    """A researcher reads this as fact, so it cannot echo arbitrary text."""
    record = provenance.build(source_system="Trusted Regional Cancer Centre EHR")
    assert record["source_system"] == "unknown"


@pytest.mark.parametrize("system", sorted(provenance.KNOWN_SOURCE_SYSTEMS))
def test_every_known_system_is_kept_verbatim(system):
    assert provenance.build(source_system=system)["source_system"] == system


def test_a_long_resource_type_is_truncated_not_echoed():
    record = provenance.build(source_system="patient_entered", resource_type="x" * 500)
    assert len(record["resource_type"]) <= 60


# ---------------------------------------------------------------------------
# The export split
# ---------------------------------------------------------------------------

def test_the_digest_never_reaches_a_recipient():
    """Inside the server it is an integrity check. Exported, it is a key."""
    record = provenance.build(source_system="synthetic_fhir_bundle",
                              resource_type="Condition", raw=RESOURCE)
    shared = provenance.exportable(record)
    assert "source_digest" not in shared
    assert record["source_digest"] not in json.dumps(shared)


def test_what_a_researcher_does_get_is_enough_to_appraise_the_data():
    record = provenance.build(source_system="synthetic_fhir_bundle",
                              resource_type="Condition", raw=RESOURCE)
    shared = provenance.exportable(record)
    assert shared["source_system"] == "synthetic_fhir_bundle"
    assert shared["parser_version"] == provenance.PARSER_VERSION
    assert shared["ingested_at"]


def test_a_record_with_no_provenance_is_reported_as_unknown_not_omitted():
    """Records predating this must read as unknown origin, never as trusted."""
    assert provenance.exportable(None)["source_system"] == "unknown"
    assert "not recorded" in provenance.describe_for_patient(None)


def test_the_summary_counts_by_system_and_names_no_record():
    entries = [
        provenance.build(source_system="synthetic_fhir_bundle", raw={"a": 1}),
        provenance.build(source_system="synthetic_fhir_bundle", raw={"a": 2}),
        provenance.build(source_system="patient_entered"),
    ]
    summary = provenance.summarize(entries)
    assert summary["records_by_source_system"] == {
        "patient_entered": 1, "synthetic_fhir_bundle": 2}
    assert provenance.PARSER_VERSION in summary["parser_versions"]
    for entry in entries:
        if entry["source_digest"]:
            assert entry["source_digest"] not in json.dumps(summary)


# ---------------------------------------------------------------------------
# Through the parser and out to the patient
# ---------------------------------------------------------------------------

def test_a_parsed_fhir_record_arrives_with_its_origin():
    from api.fhir_ingest import parse_fhir_bundle

    bundle = {"entry": [{"resource": RESOURCE | {"onsetDateTime": "2020-05-04"}}]}
    records = parse_fhir_bundle(bundle)
    assert records, "the bundle should yield a record"
    for record in records:
        origin = record["provenance"]
        assert origin["source_system"] == "synthetic_fhir_bundle"
        assert origin["parser_version"] == provenance.PARSER_VERSION
        assert origin["source_digest"]


def test_parsing_never_leaks_the_source_id_into_the_record():
    from api.fhir_ingest import parse_fhir_bundle

    bundle = {"entry": [{"resource": RESOURCE | {"onsetDateTime": "2020-05-04"}}]}
    serialized = json.dumps(parse_fhir_bundle(bundle))
    assert "hospital-record-99887766" not in serialized
    assert "mrn-12345" not in serialized


def test_a_patient_is_told_where_each_record_came_from(client, make_user):
    from api.models import ExtractedMedicalData, PatientProfile

    headers, user_id = make_user("prov-patient@example.com", role="patient")
    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id).one()
        db.add(ExtractedMedicalData(
            patient_id=profile.id, connection_id="synthetic",
            data_category="diagnosis", original_year=2020,
            deidentified_data={"display": "AML"},
            provenance=provenance.build(source_system="synthetic_fhir_bundle",
                                        resource_type="Condition", raw=RESOURCE)))
        db.commit()

    rows = client.get("/api/patient/extracted-data", headers=headers).json()
    assert rows[0]["origin"] == "Imported from a health record file you uploaded."
    # And the digest stays on the server.
    assert "source_digest" not in json.dumps(rows)


# ---------------------------------------------------------------------------
# Manifests written before this change are still true records
# ---------------------------------------------------------------------------

def test_an_older_manifest_still_verifies():
    """Adding a field must not make every prior release read as tampered."""
    from api.release_manifest import (KNOWN_SCHEMA_VERSIONS, manifest_digest,
                                      verify_manifest)

    old = {
        "schema_version": 1, "job_id": "j", "study_id": "s", "study_name": "S",
        "released_to": "u", "released_at": "2026-01-01T00:00:00",
        "deidentification_level": "limited_dataset", "variables": ["a"],
        "subject_count": 11, "record_count": 11, "content_digest": "abc",
        "cohort_criteria": None, "disclosure_risk": None, "approvals": [],
    }
    assert 1 in KNOWN_SCHEMA_VERSIONS
    assert verify_manifest(old, manifest_digest(old)) is True


def test_a_manifest_from_an_unknown_schema_does_not_verify():
    from api.release_manifest import manifest_digest, verify_manifest

    future = {"schema_version": 99, "job_id": "j"}
    assert verify_manifest(future, manifest_digest(future)) is False


def test_the_audit_notices_records_with_no_recorded_origin(client):
    """Catches a future ingest path that forgets to record where data came from."""
    from api.models import ExtractedMedicalData, PatientProfile
    from api.self_audit import WARNING, check_records_carry_provenance

    with client._session_factory() as db:
        assert check_records_carry_provenance(db).passed is True

        patient = PatientProfile()
        db.add(patient)
        db.flush()
        db.add(ExtractedMedicalData(
            patient_id=patient.id, connection_id="synthetic",
            data_category="diagnosis", original_year=2020,
            deidentified_data={"display": "AML"}, provenance=None))
        db.commit()

        finding = check_records_carry_provenance(db)

    assert finding.passed is False
    assert finding.count == 1
    # A warning: history cannot be fixed, and a permanently red audit is one
    # nobody reads.
    assert finding.severity == WARNING
