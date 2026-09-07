"""The extraction pipeline must refuse to release a re-identifiable extract.

Removing names and dates is not de-identification. A row that is unique on its
year, stage and diagnosis is linkable to a person by anyone holding a registry,
an obituary or an employment record. These tests hold the gate that stops such
an extract leaving the system, and check that the numbers behind the decision
are recorded rather than merely asserted.
"""
import csv
import io
import os

import pytest


def build_study(client, headers, patients, *, stage="II", years=None):
    """Create an approved study enrolling `patients` consented subjects."""
    from api.models import (
        Consent, ExtractedMedicalData, PatientProfile,
        RegulatorySubmission, StudyEnrollment,
    )

    created = client.post("/api/researcher/studies", headers=headers,
                          json={"name": "Disclosure gate study"})
    assert created.status_code == 200, created.text
    study_id = created.json()["id"]

    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol", status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua", status="signed"),
        ])
        for index in range(patients):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            db.add_all([
                Consent(patient_id=patient.id, consent_type="research_data_sharing", status="active"),
                StudyEnrollment(study_id=study_id, patient_id=patient.id, status="enrolled"),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="synthetic-connection",
                    data_category="diagnosis",
                    original_year=(years[index] if years else 2020),
                    deidentified_data={"stage": stage},
                ),
            ])
        db.commit()
    return study_id


def run_extraction(client, headers, study_id):
    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    assert response.status_code == 200, response.text
    return response.json()


def job_record(client, headers, job_id):
    listing = client.get("/api/extraction/jobs", headers=headers)
    assert listing.status_code == 200, listing.text
    matches = [job for job in listing.json() if job["id"] == job_id]
    assert matches, "job should appear in the researcher's job list"
    return matches[0]


def test_single_subject_extract_is_blocked(client, make_user, monkeypatch):
    """One subject is one identifiable person, whatever the fields say."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-single@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=1)
    result = run_extraction(client, headers, study_id)

    assert result["status"] == "failed"
    assert "Disclosure risk above threshold" in result["message"]


def test_blocked_extract_produces_no_downloadable_file(client, make_user, monkeypatch):
    """A blocked job must not leave a CSV behind for the download route."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-nofile@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=3)
    result = run_extraction(client, headers, study_id)
    assert result["status"] == "failed"

    download = client.get(f"/api/extraction/jobs/{result['job_id']}/download", headers=headers)
    assert download.status_code != 200
    assert "stage" not in download.text


def test_extract_at_the_threshold_is_released(client, make_user, monkeypatch):
    """Enough indistinguishable subjects and the same request succeeds."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-pass@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=11)
    result = run_extraction(client, headers, study_id)

    assert result["status"] == "completed", result
    download = client.get(f"/api/extraction/jobs/{result['job_id']}/download", headers=headers)
    assert download.status_code == 200
    rows = list(csv.DictReader(io.StringIO(download.text)))
    assert len(rows) == 11


def test_one_outlier_year_blocks_an_otherwise_large_cohort(client, make_user, monkeypatch):
    """The gate is per equivalence class, not per export size.

    Twelve subjects clear a naive count check, but the one subject recorded in
    a different year stands alone and is the person who gets re-identified.
    """
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-outlier@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=12, years=[2020] * 11 + [1974])
    result = run_extraction(client, headers, study_id)

    assert result["status"] == "failed"
    assert "1 subject(s) affected" in result["message"]


def test_the_measurement_is_recorded_on_the_job(client, make_user, monkeypatch):
    """A reviewer needs the numbers behind a block, not just the verdict."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-report@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=2)
    result = run_extraction(client, headers, study_id)

    risk = job_record(client, headers, result["job_id"])["disclosure_risk"]
    assert risk is not None, "the risk report must be persisted"
    assert risk["meets_threshold"] is False
    assert risk["min_k"] == 2
    assert risk["threshold_k"] == 11
    assert risk["unit"] == "subject"
    assert "not a compliance determination" in risk["caveat"]


def test_the_measurement_is_recorded_when_the_export_passes(client, make_user, monkeypatch):
    """Evidence of a pass matters as much as evidence of a block."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    # The variable inventory has its own small-cell floor. Lower it so each
    # test isolates the export gate rather than the inventory suppression.
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    headers, _ = make_user("gate-passreport@example.com", role="researcher", verified=True, approved=True)
    study_id = build_study(client, headers, patients=11)
    result = run_extraction(client, headers, study_id)
    assert result["status"] == "completed"

    risk = job_record(client, headers, result["job_id"])["disclosure_risk"]
    assert risk["meets_threshold"] is True
    assert risk["min_k"] == 11
    assert risk["subject_count"] == 11


def test_default_threshold_is_not_permissive():
    """A deployment that sets nothing must still get a real floor.

    MIN_EXPORT_K defaults to the aggregate small-cell floor; a default of 1
    would make the gate decorative.
    """
    import api.main as main
    assert main.MIN_EXPORT_K >= 11
    assert "MIN_EXPORT_K" not in os.environ, (
        "the test environment must not be relaxing the production default"
    )
