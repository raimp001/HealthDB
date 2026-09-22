"""A cited release must be checkable against its own bytes.

A finding cites a release digest so a reader can hold the result to the data
behind it. The manifest check proves a manifest still hashes to itself, which
is the manifest checking itself; nothing re-hashed the file it describes. An
extract whose stored content had drifted would keep an intact manifest, keep
its citation, and say nothing.

The other half of these tests is one distinction: **unverifiable is not
verified.** A release whose file is gone cannot be checked, and saying so is
the only honest answer. Collapsing it into a pass is the same failure as a
record with no date reading identically to one whose date was nonsense.
"""
from types import SimpleNamespace

import pytest

from api.release_integrity import (MISMATCH, UNVERIFIABLE, VERIFIED,
                                   verify_content)
from api.release_manifest import digest

CSV = "patient_pseudonym,data_category\nP-abc,diagnosis\n"


def release(content=CSV, release_id="r1"):
    return SimpleNamespace(id=release_id, content_digest=digest(content))


def job(content=CSV):
    return SimpleNamespace(result_csv=content)


# ---------------------------------------------------------------------------
# The three states
# ---------------------------------------------------------------------------

def test_matching_bytes_verify():
    check = verify_content(release(), job())
    assert check.state == VERIFIED and check.ok is True


def test_changed_bytes_are_a_mismatch():
    check = verify_content(release(), job(CSV + "P-def,diagnosis\n"))
    assert check.state == MISMATCH
    assert check.ok is False
    assert "cites bytes that have changed" in check.explain()


def test_a_single_changed_character_is_caught():
    check = verify_content(release(), job(CSV.replace("P-abc", "P-abd")))
    assert check.state == MISMATCH


def test_a_missing_file_is_unverifiable_not_verified():
    """The distinction the module exists to preserve."""
    check = verify_content(release(), job(None))
    assert check.state == UNVERIFIABLE
    assert check.ok is False, "unverifiable must never read as a pass"
    assert "not a pass" in check.explain()


def test_a_missing_job_is_unverifiable():
    assert verify_content(release(), None).state == UNVERIFIABLE


def test_a_release_with_no_recorded_digest_is_unverifiable():
    """An absent expectation is not a met one."""
    bare = SimpleNamespace(id="r1", content_digest=None)
    assert verify_content(bare, job()).state == UNVERIFIABLE


def test_the_computed_digest_is_reported_only_when_one_was_taken():
    assert verify_content(release(), job()).computed_digest is not None
    assert verify_content(release(), None).computed_digest is None


def test_the_payload_never_carries_the_file():
    """A verdict about bytes, not the bytes."""
    payload = str(verify_content(release(), job()).as_dict())
    assert "P-abc" not in payload
    assert "diagnosis" not in payload


# ---------------------------------------------------------------------------
# Through a real release
# ---------------------------------------------------------------------------

def released_study(client, headers, patients=12):
    """An approved study with an extract actually produced."""
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            RegulatorySubmission, StudyEnrollment)

    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": "Integrity study"}).json()["id"]
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol",
                                 status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua",
                                 status="signed"),
        ])
        for _ in range(patients):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            db.add_all([
                Consent(patient_id=patient.id,
                        consent_type="research_data_sharing", status="active"),
                StudyEnrollment(study_id=study_id, patient_id=patient.id,
                                status="enrolled"),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="synthetic",
                    data_category="diagnosis", original_year=2020,
                    deidentified_data={"stage": "II"}),
            ])
        db.commit()

    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed", response.json()
    return response.json()["job_id"]


def release_id_for(client, job_id):
    from api.models import DataRelease
    with client._session_factory() as db:
        return str(db.query(DataRelease).filter(
            DataRelease.job_id == job_id).one().id)


@pytest.fixture()
def researcher(client, make_user, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, user_id = make_user("integrity@example.com", role="researcher",
                                 verified=True, approved=True)
    return headers, user_id


def test_a_fresh_release_verifies(client, researcher):
    headers, _ = researcher
    job_id = released_study(client, headers)
    body = client.get(f"/api/releases/{release_id_for(client, job_id)}/verify",
                      headers=headers).json()
    assert body["state"] == "verified"
    assert body["verified"] is True
    assert body["manifest_intact"] is True


def test_a_tampered_extract_is_caught(client, researcher):
    """The gap this closes: the manifest stays intact while the file changes."""
    from api.models import ExtractionJob

    headers, _ = researcher
    job_id = released_study(client, headers)
    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        job.result_csv = job.result_csv + "P-forged,diagnosis,condition,2020,100.0,{}\n"
        db.commit()

    body = client.get(f"/api/releases/{release_id_for(client, job_id)}/verify",
                      headers=headers).json()
    assert body["state"] == "mismatch"
    assert body["verified"] is False
    # And the manifest still verifies, which is why this check had to exist.
    assert body["manifest_intact"] is True


def test_the_audit_blocks_on_a_tampered_release(client, researcher):
    from api.models import ExtractionJob
    from api.self_audit import check_released_content_matches_its_digest

    headers, _ = researcher
    job_id = released_study(client, headers)
    with client._session_factory() as db:
        assert check_released_content_matches_its_digest(db).passed

        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        job.result_csv = "replaced\n"
        db.commit()

        finding = check_released_content_matches_its_digest(db)
    assert not finding.passed
    assert finding.severity == "blocker"
    assert finding.count == 1


def test_the_audit_counts_unverifiable_releases_separately(client, researcher):
    """They are not failures, and they are not passes either."""
    from api.models import ExtractionJob
    from api.self_audit import check_released_content_matches_its_digest

    headers, _ = researcher
    job_id = released_study(client, headers)
    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        job.result_csv = None
        db.commit()

        finding = check_released_content_matches_its_digest(db)
    assert finding.passed          # nothing is known to be wrong
    assert finding.detail["unverifiable"] == 1
    assert finding.detail["verified"] == 0
    assert "cannot be checked" in finding.summary


def test_another_researcher_cannot_verify_someone_elses_release(client, researcher, make_user):
    """And cannot tell a release they may not see from one that does not exist.

    Distinguishing the two would let anyone holding an id learn whether it
    names a real release, and who has released what is not public.
    """
    headers, _ = researcher
    job_id = released_study(client, headers)
    other, _ = make_user("bystander@example.com", role="researcher",
                         verified=True, approved=True)

    theirs = client.get(f"/api/releases/{release_id_for(client, job_id)}/verify",
                        headers=other)
    invented = client.get(
        "/api/releases/2b1e0c4a-0000-4000-8000-000000000000/verify",
        headers=other)
    assert theirs.status_code == 404
    assert theirs.status_code == invented.status_code
    assert theirs.json() == invented.json()


def test_an_admin_can_verify_any_release(client, researcher, make_user):
    headers, _ = researcher
    job_id = released_study(client, headers)
    admin, _ = make_user("integrity-admin@example.com", role="admin", verified=True)
    response = client.get(f"/api/releases/{release_id_for(client, job_id)}/verify",
                          headers=admin)
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "verified"
