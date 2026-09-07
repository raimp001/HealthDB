"""The whole loop: consent, release, download, revoke, obligation.

Each piece is unit-tested elsewhere. This checks they are actually wired to
each other, which is where this kind of system usually fails — every part
works and nothing is connected.
"""
import csv
import io
from datetime import datetime

import pytest

from tests.conftest import VALID_PASSWORD


def enrolled_study(client, headers, patients=11):
    """An approved study with `patients` consented, enrolled subjects."""
    from api.models import (
        Consent, ExtractedMedicalData, PatientProfile,
        RegulatorySubmission, StudyEnrollment,
    )

    created = client.post("/api/researcher/studies", headers=headers,
                          json={"name": "Lifecycle study"})
    assert created.status_code == 200, created.text
    study_id = created.json()["id"]

    patient_ids = []
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol", status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua", status="signed"),
        ])
        for _ in range(patients):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            patient_ids.append(str(patient.id))
            db.add_all([
                Consent(patient_id=patient.id, consent_type="research_data_sharing", status="active"),
                StudyEnrollment(study_id=study_id, patient_id=patient.id, status="enrolled"),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="synthetic-connection",
                    data_category="diagnosis", original_year=2020,
                    deidentified_data={"stage": "II"},
                ),
            ])
        db.commit()
    return study_id, patient_ids


@pytest.fixture()
def researcher(client, make_user, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, user_id = make_user("lifecycle@example.com", role="researcher",
                                 verified=True, approved=True)
    return headers, user_id


def create_and_download(client, headers, study_id):
    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    assert response.status_code == 200, response.text
    job = response.json()
    assert job["status"] == "completed", job
    download = client.get(f"/api/extraction/jobs/{job['job_id']}/download", headers=headers)
    assert download.status_code == 200, download.text
    return job, download


def test_a_release_is_recorded_and_matches_the_file(client, researcher):
    """The digest handed to the recipient must match the bytes they received."""
    from api.models import DataRelease
    from api.release_manifest import digest, verify_manifest

    headers, user_id = researcher
    study_id, _ = enrolled_study(client, headers)
    job, download = create_and_download(client, headers, study_id)

    with client._session_factory() as db:
        release = db.query(DataRelease).filter(DataRelease.job_id == job["job_id"]).one()
        assert release.content_digest == digest(download.text)
        assert verify_manifest(release.manifest, release.manifest_digest)
        assert release.subject_count == 11
        assert release.manifest["disclosure_risk"]["meets_threshold"] is True
        # The approvals that authorized this release are part of the record.
        types = {a["document_type"] for a in release.manifest["approvals"]}
        assert {"irb_protocol", "dua"}.issubset(types)

    assert download.headers.get("X-Content-Digest") == f"sha256={digest(download.text)}"


def test_the_download_is_what_gets_metered_not_the_extract(client, researcher):
    """Building an extract and handing it over are different events."""
    from api.models import DataRelease

    headers, _ = researcher
    study_id, _ = enrolled_study(client, headers)

    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    job_id = response.json()["job_id"]

    with client._session_factory() as db:
        release = db.query(DataRelease).filter(DataRelease.job_id == job_id).one()
        assert release.download_count == 0
        assert release.first_downloaded_at is None
        assert release.license_state == "not_licensed"

    client.get(f"/api/extraction/jobs/{job_id}/download", headers=headers)
    client.get(f"/api/extraction/jobs/{job_id}/download", headers=headers)

    with client._session_factory() as db:
        release = db.query(DataRelease).filter(DataRelease.job_id == job_id).one()
        assert release.download_count == 2
        assert release.first_downloaded_at is not None
        assert release.last_downloaded_at >= release.first_downloaded_at


def test_a_download_is_written_to_the_patient_access_log(client, researcher):
    from api.models import DataAccessLog

    headers, _ = researcher
    study_id, patient_ids = enrolled_study(client, headers)
    create_and_download(client, headers, study_id)

    with client._session_factory() as db:
        logged = db.query(DataAccessLog).filter(
            DataAccessLog.access_type == "research_export_download"
        ).all()
    assert {log.patient_id for log in logged} == set(patient_ids)


def test_revocation_flags_the_release_and_tells_the_patient(client, researcher, make_user):
    """Revoking cannot recall a downloaded file. It must say so, not pretend."""
    from api.models import Consent, DataRelease, PatientProfile, User

    from api.models import ExtractedMedicalData, StudyEnrollment

    headers, _ = researcher
    # A real patient login, enrolled alongside the synthetic subjects, so the
    # revocation runs through the actual HTTP path rather than a DB write.
    patient_headers, patient_user_id = make_user("lifecycle-patient@example.com", role="patient")
    study_id, _ = enrolled_study(client, headers, patients=10)
    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == patient_user_id).one()
        consent = Consent(patient_id=profile.id,
                          consent_type="research_data_sharing", status="active")
        db.add_all([
            consent,
            StudyEnrollment(study_id=study_id, patient_id=profile.id, status="enrolled"),
            ExtractedMedicalData(
                patient_id=profile.id, connection_id="synthetic-connection",
                data_category="diagnosis", original_year=2020,
                deidentified_data={"stage": "II"},
            ),
        ])
        db.commit()
        consent_id = consent.id

    job, _ = create_and_download(client, headers, study_id)

    revoked = client.post(f"/api/consent/{consent_id}/revoke", headers=patient_headers)
    assert revoked.status_code == 200, revoked.text
    body = revoked.json()
    assert body["prior_releases"] == 1
    assert body["prior_releases_downloaded"] == 1
    assert body["outstanding_obligation"] is True
    assert "cannot be recalled" in body["note"]

    with client._session_factory() as db:
        release = db.query(DataRelease).filter(DataRelease.job_id == job["job_id"]).one()
        assert release.withdrawal_required_at is not None

    # The patient can see which releases carried their data.
    releases = client.get("/api/patient/data-releases", headers=patient_headers)
    assert releases.status_code == 200, releases.text
    assert len(releases.json()) == 1
    assert releases.json()[0]["withdrawal_required"] is True
    assert releases.json()[0]["downloaded"] is True

    # And the researcher holding it is told what to do about it.
    obligations = client.get("/api/researcher/release-obligations", headers=headers)
    assert obligations.status_code == 200, obligations.text
    assert len(obligations.json()) == 1
    assert "Destroy your local copy" in obligations.json()[0]["action_required"]


def test_revoking_with_no_prior_release_says_so(client, make_user):
    from api.models import Consent, PatientProfile

    patient_headers, patient_user_id = make_user("clean-revoke@example.com", role="patient")
    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == patient_user_id).one()
        consent = Consent(patient_id=profile.id,
                          consent_type="research_data_sharing", status="active")
        db.add(consent)
        db.commit()
        consent_id = consent.id

    body = client.post(f"/api/consent/{consent_id}/revoke", headers=patient_headers).json()
    assert body["prior_releases"] == 0
    assert body["outstanding_obligation"] is False
    assert "No extract containing your data has been downloaded." in body["note"]


def test_a_patient_only_sees_releases_containing_their_own_data(client, researcher, make_user):
    headers, _ = researcher
    study_id, _ = enrolled_study(client, headers)
    create_and_download(client, headers, study_id)

    outsider_headers, _ = make_user("outsider@example.com", role="patient")
    releases = client.get("/api/patient/data-releases", headers=outsider_headers)
    assert releases.status_code == 200
    assert releases.json() == []


def test_the_audit_passes_after_a_clean_release(client, researcher):
    """The invariants must hold on data the system itself produced."""
    from api.self_audit import run_audit

    headers, _ = researcher
    study_id, _ = enrolled_study(client, headers)
    create_and_download(client, headers, study_id)

    with client._session_factory() as db:
        report = run_audit(db)
    assert report.ok, report.summary()


def test_the_audit_catches_the_revocation_the_moment_it_is_unflagged(client, researcher):
    """Undo the flag and the auditor must notice, not take the DB's word."""
    from api.models import Consent, DataRelease
    from api.self_audit import run_audit

    headers, _ = researcher
    study_id, patient_ids = enrolled_study(client, headers)
    create_and_download(client, headers, study_id)

    with client._session_factory() as db:
        db.query(Consent).filter(Consent.patient_id == patient_ids[0]).update(
            {"status": "revoked", "revoked_at": datetime.utcnow()})
        db.commit()
        report = run_audit(db)

    assert report.ok is False
    assert any(f.name == "revocations_are_tracked" for f in report.blockers)
