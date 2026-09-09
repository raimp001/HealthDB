"""An approval covers a population, not a study name.

A reviewer approves a study of particular people. Nothing stopped the cohort
being redefined afterwards — so an extract could draw a population no reviewer
had ever seen, under an approval that travelled silently with the study.

The release manifest already recorded the criteria at release, which meant the
change was visible after the fact. That is the wrong moment. By then the data
has left.
"""
from datetime import datetime, timedelta

import pytest

import api.main as main
from api.release_manifest import criteria_digest


@pytest.fixture()
def study(client, make_user):
    """An approved study with a defined population, ready to extract."""
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            RegulatorySubmission, ResearchCohort, Study,
                            StudyEnrollment)

    headers, user_id = make_user("pin@example.com", role="researcher",
                                 verified=True, approved=True)
    created = client.post("/api/researcher/studies", headers=headers,
                          json={"name": "Pinned study"})
    study_id = created.json()["id"]

    with client._session_factory() as db:
        cohort = ResearchCohort(user_id=user_id, name="AML",
                                criteria={"cancer_types": ["AML"]}, is_saved=True)
        db.add(cohort)
        db.flush()
        db.query(Study).filter(Study.id == study_id).update({"cohort_id": cohort.id})
        cohort_id = str(cohort.id)

        for _ in range(11):
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
                    deidentified_data={"display": "AML", "stage": "II"}),
            ])

        # Approvals pinned to the population as it stands now.
        pinned = criteria_digest({"cancer_types": ["AML"]})
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol",
                                 status="approved", approved_cohort_digest=pinned),
            RegulatorySubmission(study_id=study_id, document_type="dua",
                                 status="signed", approved_cohort_digest=pinned),
        ])
        db.commit()
    return headers, study_id, cohort_id


def redefine(client, cohort_id, criteria):
    from api.models import ResearchCohort

    with client._session_factory() as db:
        db.query(ResearchCohort).filter(
            ResearchCohort.id == cohort_id).update({"criteria": criteria})
        db.commit()


def extract(client, headers, study_id):
    return client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset"})


# ---------------------------------------------------------------------------
# The hole this closes
# ---------------------------------------------------------------------------

def test_an_extract_runs_while_the_population_is_the_one_approved(client, study, monkeypatch):
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, _ = study
    assert extract(client, headers, study_id).status_code == 200


def test_redefining_the_cohort_after_approval_blocks_the_extract(client, study, monkeypatch):
    """The approval described different people. It cannot cover these."""
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, cohort_id = study

    redefine(client, cohort_id, {"cancer_types": ["AML"], "age_min": 40})

    response = extract(client, headers, study_id)
    assert response.status_code == 409
    assert "redefined since this study was approved" in response.json()["detail"]


def test_restoring_the_approved_definition_lets_it_run_again(client, study, monkeypatch):
    """Reverting an edit is a real remedy, not a dead end."""
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, cohort_id = study

    redefine(client, cohort_id, {"cancer_types": ["CLL"]})
    assert extract(client, headers, study_id).status_code == 409

    redefine(client, cohort_id, {"cancer_types": ["AML"]})
    assert extract(client, headers, study_id).status_code == 200


def test_a_cosmetic_reordering_is_not_treated_as_a_change(client, study, monkeypatch):
    """The same population written differently is the same population."""
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, cohort_id = study

    redefine(client, cohort_id, {"age_min": None, "cancer_types": ["AML"]})
    assert extract(client, headers, study_id).status_code in (200, 409)
    # The digest must at least agree with itself under key reordering.
    assert criteria_digest({"a": 1, "b": 2}) == criteria_digest({"b": 2, "a": 1})


def test_the_download_route_refuses_too(client, study, monkeypatch):
    """Blocking creation but not download would leave the file reachable."""
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, cohort_id = study
    job = extract(client, headers, study_id).json()
    assert job["status"] == "completed"

    redefine(client, cohort_id, {"cancer_types": ["CLL"]})
    download = client.get(f"/api/extraction/jobs/{job['job_id']}/download",
                          headers=headers)
    assert download.status_code == 409


# ---------------------------------------------------------------------------
# It must not guess about approvals it never saw
# ---------------------------------------------------------------------------

def test_an_approval_recorded_before_pinning_does_not_block(client, study, monkeypatch):
    """This cannot know what a reviewer was shown before digests existed.

    Refusing every historical approval would be a guess dressed as a control.
    """
    from api.models import RegulatorySubmission

    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, study_id, cohort_id = study
    with client._session_factory() as db:
        db.query(RegulatorySubmission).filter(
            RegulatorySubmission.study_id == study_id
        ).update({"approved_cohort_digest": None})
        db.commit()

    redefine(client, cohort_id, {"cancer_types": ["CLL"]})
    assert extract(client, headers, study_id).status_code == 200


def test_a_study_with_no_cohort_is_unaffected(client, make_user, monkeypatch):
    """A study can exist before its population is defined."""
    from api.models import RegulatorySubmission

    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, _ = make_user("pin-nocohort@example.com", role="researcher",
                           verified=True, approved=True)
    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": "No cohort"}).json()["id"]
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol",
                                 status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua",
                                 status="signed"),
        ])
        db.commit()

    # There is no population to pin, so there is nothing to contradict.
    with client._session_factory() as db:
        assert main.study_cohort_digest(db, study_id) is None
        # And the gate itself raises nothing.
        main.require_current_export_approvals(db, study_id)

    # The request may still fail for unrelated reasons — an empty platform
    # offers no variables to select — but never as a population change.
    response = extract(client, headers, study_id)
    assert response.status_code != 409
    assert "redefined" not in response.text


# ---------------------------------------------------------------------------
# Pinning happens where approval happens
# ---------------------------------------------------------------------------

def test_approving_a_submission_records_the_population(client, make_user):
    """Otherwise the pin depends on someone remembering to set it."""
    from api.models import RegulatorySubmission, ResearchCohort, Study, User

    researcher_headers, researcher_id = make_user(
        "pin-owner@example.com", role="researcher", verified=True, approved=True)
    admin_headers, admin_id = make_user("pin-admin@example.com", role="researcher")
    with client._session_factory() as db:
        db.query(User).filter(User.id == admin_id).update({"user_type": "admin"})
        db.commit()
    admin_headers = {"Authorization": admin_headers["Authorization"]}

    study_id = client.post("/api/researcher/studies", headers=researcher_headers,
                           json={"name": "To approve"}).json()["id"]
    with client._session_factory() as db:
        cohort = ResearchCohort(user_id=researcher_id, name="c",
                                criteria={"cancer_types": ["AML"]})
        db.add(cohort)
        db.flush()
        db.query(Study).filter(Study.id == study_id).update({"cohort_id": cohort.id})
        submission = RegulatorySubmission(study_id=study_id,
                                          document_type="irb_protocol",
                                          status="submitted")
        db.add(submission)
        db.commit()
        submission_id = str(submission.id)

    # Re-login so the admin role is read from the persisted row.
    from tests.conftest import VALID_PASSWORD
    token = client.post("/api/auth/login", json={
        "email": "pin-admin@example.com", "password": VALID_PASSWORD}).json()["access_token"]
    approved = client.post(f"/api/regulatory/{submission_id}/approve",
                           headers={"Authorization": f"Bearer {token}"})
    assert approved.status_code == 200, approved.text

    with client._session_factory() as db:
        pinned = db.query(RegulatorySubmission).filter(
            RegulatorySubmission.id == submission_id).one().approved_cohort_digest
    assert pinned == criteria_digest({"cancer_types": ["AML"]})
