"""A study that changes has to ask again.

Somebody joins a study about one thing. Months later the purpose is
rewritten, the population redrawn, or the variables grow to include their
molecular profile. Nobody asks them again, and the platform carries on — which
is the quietest way a research platform becomes extractive.

The load-bearing test here is not that the question gets asked. It is that
not answering keeps the person *out*. A re-consent screen that leaves records
flowing while it waits is an announcement wearing a question's clothes.
"""
from datetime import datetime

import pytest

import api.main as main
from api.study_scope import describe_change, scope_of


@pytest.fixture()
def enrolled(client, make_user, monkeypatch):
    """A patient enrolled in a study, with records eligible for extract."""
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            ResearchCohort, Study, StudyEnrollment)

    monkeypatch.setattr(main, "PATIENT_STUDY_ENROLLMENT_ENABLED", True)
    researcher_headers, researcher_id = make_user(
        "rc-pi@example.com", role="researcher", verified=True, approved=True)
    patient_headers, patient_user_id = make_user("rc-patient@example.com",
                                                 role="patient")

    study_id = client.post("/api/researcher/studies", headers=researcher_headers,
                           json={"name": "Remission duration"}).json()["id"]

    with client._session_factory() as db:
        cohort = ResearchCohort(user_id=researcher_id, name="AML",
                                criteria={"cancer_types": ["AML"]})
        db.add(cohort)
        db.flush()
        db.query(Study).filter(Study.id == study_id).update({
            "cohort_id": cohort.id, "description": "Study remission duration",
            "eligibility_summary": "Adults treated for AML",
            "selected_variables": ["diagnosis.stage"], "is_recruiting": True})
        cohort_id = str(cohort.id)

        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == patient_user_id).one()
        db.add_all([
            Consent(patient_id=profile.id,
                    consent_type="research_data_sharing", status="active"),
            ExtractedMedicalData(patient_id=profile.id, connection_id="synthetic",
                                 data_category="diagnosis", original_year=2020,
                                 deidentified_data={"display": "AML"}),
        ])
        db.commit()
        patient_id = str(profile.id)

        # Enrol through the real helper so the baseline is recorded the way
        # joining records it.
        study = db.query(Study).filter(Study.id == study_id).one()
        enrollment = StudyEnrollment(study_id=study_id, patient_id=patient_id,
                                     status="enrolled")
        db.add(enrollment)
        main.record_consented_scope(db, enrollment, study)
        db.commit()

    return {"patient": patient_headers, "study_id": study_id,
            "cohort_id": cohort_id, "patient_id": patient_id}


def change(client, study_id, **fields):
    from api.models import Study

    with client._session_factory() as db:
        db.query(Study).filter(Study.id == study_id).update(fields)
        db.commit()


def eligible_ids(client, study_id):
    from api.models import Study

    with client._session_factory() as db:
        study = db.query(Study).filter(Study.id == study_id).one()
        return {str(r.patient_id) for r in main.eligible_export_records(db, study)}


# ---------------------------------------------------------------------------
# The part that makes it real
# ---------------------------------------------------------------------------

def test_an_unchanged_study_asks_nothing(client, enrolled):
    assert client.get("/api/patient/reconsent",
                      headers=enrolled["patient"]).json() == []


def test_records_stay_eligible_while_the_study_is_the_one_they_joined(client, enrolled):
    assert enrolled["patient_id"] in eligible_ids(client, enrolled["study_id"])


def test_a_changed_purpose_removes_them_from_the_pool_immediately(client, enrolled):
    """Not after they decline. While the question is open."""
    change(client, enrolled["study_id"], description="Study something else entirely")
    assert enrolled["patient_id"] not in eligible_ids(client, enrolled["study_id"])


def test_not_answering_keeps_them_out(client, enrolled):
    """Silence is not consent. This is the whole design."""
    change(client, enrolled["study_id"], description="A different question")
    pending = client.get("/api/patient/reconsent", headers=enrolled["patient"]).json()
    assert len(pending) == 1

    # Time passes; nobody answers.
    assert enrolled["patient_id"] not in eligible_ids(client, enrolled["study_id"])


def test_continuing_puts_them_back(client, enrolled):
    change(client, enrolled["study_id"], description="A different question")
    response = client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                           headers=enrolled["patient"], json={"decision": "continue"})
    assert response.status_code == 200, response.text
    assert enrolled["patient_id"] in eligible_ids(client, enrolled["study_id"])
    assert client.get("/api/patient/reconsent", headers=enrolled["patient"]).json() == []


def test_withdrawing_leaves_the_study(client, enrolled):
    change(client, enrolled["study_id"], description="A different question")
    response = client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                           headers=enrolled["patient"], json={"decision": "withdraw"})
    assert response.status_code == 200, response.text
    assert enrolled["patient_id"] not in eligible_ids(client, enrolled["study_id"])
    assert client.get("/api/patient/reconsent", headers=enrolled["patient"]).json() == []


def test_continuing_once_does_not_cover_the_next_change(client, enrolled):
    """Each change is its own question."""
    change(client, enrolled["study_id"], description="Second version")
    client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                headers=enrolled["patient"], json={"decision": "continue"})

    change(client, enrolled["study_id"], description="Third version")
    assert len(client.get("/api/patient/reconsent",
                          headers=enrolled["patient"]).json()) == 1


def test_there_is_no_answer_that_means_decide_for_me(client, enrolled):
    change(client, enrolled["study_id"], description="A different question")
    for bad in ("defer", "later", "", "skip"):
        response = client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                               headers=enrolled["patient"], json={"decision": bad})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# What counts as material
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,value", [
    ("description", "A different question"),
    ("eligibility_summary", "Now for a different group"),
    ("selected_variables", ["diagnosis.stage", "molecular.marker"]),
])
def test_material_changes_reopen_the_question(client, enrolled, field, value):
    change(client, enrolled["study_id"], **{field: value})
    assert len(client.get("/api/patient/reconsent",
                          headers=enrolled["patient"]).json()) == 1


@pytest.mark.parametrize("field,value", [
    ("name", "Renamed study"),
    ("principal_investigator", "Someone else"),
    ("status", "active"),
    ("patient_count", 99),
])
def test_bookkeeping_changes_do_not(client, enrolled, field, value):
    """Consent fatigue erodes consent faster than it protects it."""
    change(client, enrolled["study_id"], **{field: value})
    assert client.get("/api/patient/reconsent",
                      headers=enrolled["patient"]).json() == []


def test_redrawing_the_population_reopens_the_question(client, enrolled):
    """Editing the cohort changes who the study is about."""
    from api.models import ResearchCohort

    with client._session_factory() as db:
        db.query(ResearchCohort).filter(
            ResearchCohort.id == enrolled["cohort_id"]
        ).update({"criteria": {"cancer_types": ["CLL"]}})
        db.commit()

    pending = client.get("/api/patient/reconsent", headers=enrolled["patient"]).json()
    assert len(pending) == 1
    assert "group of participants" in " ".join(pending[0]["changes"])


def test_reordering_selected_variables_is_not_a_change(client, enrolled):
    change(client, enrolled["study_id"], selected_variables=["diagnosis.stage"])
    assert client.get("/api/patient/reconsent",
                      headers=enrolled["patient"]).json() == []


# ---------------------------------------------------------------------------
# What the person is told
# ---------------------------------------------------------------------------

def test_they_are_told_which_kind_of_thing_changed(client, enrolled):
    change(client, enrolled["study_id"], description="A different question")
    pending = client.get("/api/patient/reconsent", headers=enrolled["patient"]).json()[0]
    assert "What the study is trying to find out has changed." in pending["changes"]


def test_they_are_told_nothing_is_happening_while_they_decide(client, enrolled):
    change(client, enrolled["study_id"], description="A different question")
    note = client.get("/api/patient/reconsent",
                      headers=enrolled["patient"]).json()[0]["note"]
    assert "not being used" in note
    assert "choosing not to answer keeps them out" in note


def test_several_changes_at_once_are_all_named():
    before = {"purpose": "a", "eligibility": "b", "variables": [], "population": None}
    after = {"purpose": "z", "eligibility": "y", "variables": ["x"], "population": None}
    assert len(describe_change(before, after)) == 3


def test_an_unrecorded_baseline_is_admitted_rather_than_guessed():
    described = describe_change(None, {"purpose": "a"})
    assert "was not recorded" in described[0]


# ---------------------------------------------------------------------------
# Enrolments predating scope tracking
# ---------------------------------------------------------------------------

def test_an_enrolment_with_no_baseline_is_not_mass_withdrawn(client, enrolled):
    """Nothing here knows what those people were shown.

    Withdrawing them all on a guess would be its own harm; the self-audit
    reports the count instead.
    """
    from api.models import StudyEnrollment

    with client._session_factory() as db:
        db.query(StudyEnrollment).filter(
            StudyEnrollment.study_id == enrolled["study_id"]
        ).update({"consented_scope_digest": None, "consented_scope": None})
        db.commit()

    change(client, enrolled["study_id"], description="Changed after the fact")
    assert client.get("/api/patient/reconsent",
                      headers=enrolled["patient"]).json() == []
    assert enrolled["patient_id"] in eligible_ids(client, enrolled["study_id"])


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------

def test_one_patient_cannot_answer_for_another(client, enrolled, make_user):
    other_headers, _ = make_user("rc-other@example.com", role="patient")
    change(client, enrolled["study_id"], description="A different question")
    response = client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                           headers=other_headers, json={"decision": "continue"})
    assert response.status_code == 404


def test_answering_an_unchanged_study_is_refused(client, enrolled):
    response = client.post(f"/api/patient/reconsent/{enrolled['study_id']}",
                           headers=enrolled["patient"], json={"decision": "continue"})
    assert response.status_code == 409


def test_a_researcher_cannot_reach_the_reconsent_routes(client, approved_researcher):
    assert client.get("/api/patient/reconsent",
                      headers=approved_researcher).status_code in (401, 403)


def test_the_audit_reports_enrolments_with_no_baseline(client, enrolled):
    from api.models import StudyEnrollment
    from api.self_audit import WARNING, check_enrolments_have_a_consent_baseline

    with client._session_factory() as db:
        assert check_enrolments_have_a_consent_baseline(db).passed is True

        db.query(StudyEnrollment).filter(
            StudyEnrollment.study_id == enrolled["study_id"]
        ).update({"consented_scope_digest": None})
        db.commit()
        finding = check_enrolments_have_a_consent_baseline(db)

    assert finding.passed is False
    assert finding.count == 1
    assert finding.severity == WARNING
