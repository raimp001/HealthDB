"""Returning findings to the people who contributed the data.

Two things must hold: a participant sees results from studies they joined,
and nobody else does. The third is framing — a finding about a group must
never reach a patient looking like guidance about their own care.
"""
import pytest

SUMMARY = (
    "Across the participants in this study, patients who received the "
    "combination regimen stayed in remission longer than those on the "
    "standard regimen. The difference was largest in people diagnosed before "
    "the age of sixty. These are group averages and individual results varied "
    "considerably."
)


@pytest.fixture()
def study_with_participant(client, make_user):
    """An approved researcher's study with one enrolled patient who can log in."""
    from api.models import PatientProfile, StudyEnrollment

    researcher_headers, _ = make_user("results-pi@example.com", role="researcher",
                                      verified=True, approved=True)
    patient_headers, patient_user_id = make_user("results-patient@example.com",
                                                 role="patient")

    created = client.post("/api/researcher/studies", headers=researcher_headers,
                          json={"name": "Remission duration study"})
    assert created.status_code == 200, created.text
    study_id = created.json()["id"]

    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == patient_user_id).one()
        db.add(StudyEnrollment(study_id=study_id, patient_id=profile.id,
                               status="enrolled"))
        db.commit()
    return study_id, researcher_headers, patient_headers


def publish(client, headers, study_id, **overrides):
    body = {"title": "Combination regimen and remission duration",
            "plain_language_summary": SUMMARY}
    body.update(overrides)
    return client.post(f"/api/researcher/studies/{study_id}/results",
                       headers=headers, json=body)


def test_a_participant_sees_the_finding_from_their_study(study_with_participant, client):
    study_id, researcher_headers, patient_headers = study_with_participant

    published = publish(client, researcher_headers, study_id)
    assert published.status_code == 200, published.text
    assert published.json()["visible_to_participants"] == 1

    results = client.get("/api/patient/study-results", headers=patient_headers)
    assert results.status_code == 200, results.text
    assert len(results.json()) == 1
    assert results.json()[0]["study_name"] == "Remission duration study"
    assert results.json()[0]["plain_language_summary"] == SUMMARY


def test_every_returned_result_is_framed_as_a_group_finding(study_with_participant, client):
    """A result must not read as advice about the reader's own care."""
    study_id, researcher_headers, patient_headers = study_with_participant
    publish(client, researcher_headers, study_id)

    result = client.get("/api/patient/study-results", headers=patient_headers).json()[0]
    assert "not advice about your own care" in result["disclaimer"]


def test_a_patient_who_did_not_join_sees_nothing(study_with_participant, client, make_user):
    study_id, researcher_headers, _ = study_with_participant
    publish(client, researcher_headers, study_id)

    outsider_headers, _ = make_user("results-outsider@example.com", role="patient")
    results = client.get("/api/patient/study-results", headers=outsider_headers)
    assert results.status_code == 200
    assert results.json() == []


def test_a_withdrawn_participant_stops_receiving_new_results(study_with_participant, client):
    """Enrolment is what grants the view, so leaving removes it."""
    from api.models import StudyEnrollment

    study_id, researcher_headers, patient_headers = study_with_participant
    publish(client, researcher_headers, study_id)

    with client._session_factory() as db:
        db.query(StudyEnrollment).filter(
            StudyEnrollment.study_id == study_id).update({"status": "withdrawn"})
        db.commit()

    assert client.get("/api/patient/study-results", headers=patient_headers).json() == []


def test_a_researcher_cannot_publish_to_someone_elses_study(study_with_participant, client, make_user):
    study_id, _, _ = study_with_participant
    other_headers, _ = make_user("results-stranger@example.com", role="researcher",
                                 verified=True, approved=True)
    assert publish(client, other_headers, study_id).status_code == 403


def test_a_patient_cannot_publish_a_result(study_with_participant, client):
    study_id, _, patient_headers = study_with_participant
    assert publish(client, patient_headers, study_id).status_code in (401, 403)


def test_a_one_line_summary_is_rejected(study_with_participant, client):
    """Someone gave years of medical history. 'It went well' is not a result."""
    study_id, researcher_headers, _ = study_with_participant
    response = publish(client, researcher_headers, study_id,
                       plain_language_summary="It went well.")
    assert response.status_code == 422


def test_the_study_team_can_review_what_participants_were_told(study_with_participant, client):
    study_id, researcher_headers, _ = study_with_participant
    publish(client, researcher_headers, study_id, citation="https://doi.org/10.0000/example")

    listed = client.get(f"/api/researcher/studies/{study_id}/results",
                        headers=researcher_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["citation"] == "https://doi.org/10.0000/example"


def test_results_are_newest_first(study_with_participant, client):
    study_id, researcher_headers, patient_headers = study_with_participant
    publish(client, researcher_headers, study_id, title="First finding")
    publish(client, researcher_headers, study_id, title="Second finding")

    titles = [r["title"] for r in
              client.get("/api/patient/study-results", headers=patient_headers).json()]
    assert titles[0] == "Second finding"
