"""An extract that could be subtracted from an earlier one is held, not released.

Small-cell suppression protects a single file. Two files whose subject sets
differ by three people identify those three to anyone holding both, and each
file on its own cleared every check.

api/query_budget.py refuses to block this across accounts for cohort *counts*,
and is right to: a control that fires on ordinary exploratory work is one
people learn to route around. A release is different. It is rare, already
gated by an IRB approval and a signed DUA, it is the moment row-level data
about real people leaves the system, and it is the only step here that cannot
be undone. So it gets the expensive control.

These tests hold three lines: nothing is built while a hold is open, the
requester is never told what it collided with, and an approval covers the
people it was granted for.
"""
import pytest

from api.release_differencing import ReleaseCollision, find_collision, subject_digest


class FakeRelease:
    def __init__(self, id, subjects, user_id="u1", study_id="s1", downloads=0):
        self.id = id
        self.subject_ids = subjects
        self.released_to_user_id = user_id
        self.study_id = study_id
        self.download_count = downloads


# ---------------------------------------------------------------------------
# What counts as a collision
# ---------------------------------------------------------------------------

def test_sets_differing_by_fewer_than_the_floor_collide():
    prior = FakeRelease("r1", [f"p{i}" for i in range(20)])
    new = [f"p{i}" for i in range(23)]          # three more people
    found = find_collision(new, [prior], threshold=11)
    assert found and found.difference == 3


def test_an_identical_set_is_not_a_collision():
    """Re-running an extract that returns the same people discloses nothing."""
    subjects = [f"p{i}" for i in range(20)]
    assert find_collision(subjects, [FakeRelease("r1", subjects)], threshold=11) is None


def test_a_set_differing_by_the_floor_or_more_is_not_a_collision():
    prior = FakeRelease("r1", [f"p{i}" for i in range(20)])
    new = [f"p{i}" for i in range(31)]          # eleven more
    assert find_collision(new, [prior], threshold=11) is None


def test_removal_counts_as_much_as_addition():
    """A subtraction works in either direction."""
    prior = FakeRelease("r1", [f"p{i}" for i in range(20)])
    new = [f"p{i}" for i in range(18)]
    found = find_collision(new, [prior], threshold=11)
    assert found and found.difference == 2


def test_a_disjoint_set_is_not_a_collision():
    """No overlap means nothing to subtract."""
    prior = FakeRelease("r1", [f"p{i}" for i in range(20)])
    assert find_collision([f"q{i}" for i in range(20)], [prior], threshold=11) is None


def test_the_shape_tells_a_reviewer_what_they_are_looking_at():
    subjects = [f"p{i}" for i in range(20)]
    new = subjects + ["p20", "p21"]
    same = find_collision(new, [FakeRelease("r1", subjects, "u1", "s1")],
                          threshold=11, requester_user_id="u1", study_id="s1")
    other_study = find_collision(new, [FakeRelease("r1", subjects, "u1", "s2")],
                                 threshold=11, requester_user_id="u1", study_id="s1")
    other_account = find_collision(new, [FakeRelease("r1", subjects, "u2", "s2")],
                                   threshold=11, requester_user_id="u1", study_id="s1")
    assert same.shape() == "same researcher, same study"
    assert other_study.shape() == "same researcher, different study"
    assert other_account.shape() == "different accounts"


# ---------------------------------------------------------------------------
# What the requester is told
# ---------------------------------------------------------------------------

def test_the_requester_is_told_nothing_about_the_other_cohort():
    """The requester is the one person who must not have this detail."""
    collision = ReleaseCollision(
        prior_release_id="release-abc", prior_subject_count=20,
        new_subject_count=23, difference=3, threshold=11,
        same_account=False, same_study=False, prior_downloaded=True)
    message = collision.for_requester()
    for leak in ["release-abc", "3", "20", "23", "11"]:
        assert leak not in message, f"requester message leaks {leak!r}: {message}"


def test_the_requester_is_not_blamed():
    """A researcher who did everything right should not read this as a fault."""
    collision = ReleaseCollision("r", 20, 23, 3, 11, False, False, False)
    message = collision.for_requester().lower()
    assert "nothing is wrong with your study" in message
    assert "nothing for you to correct" in message


def test_the_reviewer_gets_the_numbers():
    collision = ReleaseCollision("release-abc", 20, 23, 3, 11, False, False, True)
    detail = collision.for_reviewer()
    assert detail["subjects_differing"] == 3
    assert detail["prior_release_id"] == "release-abc"
    assert detail["prior_release_downloaded"] is True


# ---------------------------------------------------------------------------
# The digest that binds an approval to a set of people
# ---------------------------------------------------------------------------

def test_the_digest_ignores_ordering():
    assert subject_digest(["b", "a"]) == subject_digest(["a", "b"])


def test_the_digest_changes_when_the_people_change():
    assert subject_digest(["a", "b"]) != subject_digest(["a", "b", "c"])


# ---------------------------------------------------------------------------
# Through the extraction path
# ---------------------------------------------------------------------------

def build_study(client, headers, *, name, patients, offset=0):
    """An approved study enrolling `patients` consented subjects."""
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            RegulatorySubmission, StudyEnrollment)

    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": name}).json()["id"]
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol",
                                 status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua",
                                 status="signed"),
        ])
        existing = {str(p.id) for p in db.query(PatientProfile).all()}
        pool = sorted(existing)
        for index in range(patients):
            if offset + index < len(pool):
                patient_id = pool[offset + index]
            else:
                patient = PatientProfile()
                db.add(patient)
                db.flush()
                patient_id = str(patient.id)
                db.add_all([
                    Consent(patient_id=patient_id,
                            consent_type="research_data_sharing", status="active"),
                    ExtractedMedicalData(
                        patient_id=patient_id, connection_id="synthetic",
                        data_category="diagnosis", data_type="condition",
                        original_year=2021,
                        deidentified_data={"stage": "II"}),
                ])
            db.add(StudyEnrollment(study_id=study_id, patient_id=patient_id,
                                   status="enrolled"))
        db.commit()
    return study_id


def run_extract(client, headers, study_id):
    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    assert response.status_code == 200, response.text
    return response.json()["job_id"]


def job_state(client, headers, job_id):
    jobs = client.get("/api/extraction/jobs", headers=headers).json()
    return next(job for job in jobs if job["id"] == job_id)


@pytest.fixture()
def pi(client, make_user, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, _ = make_user("pi@example.com", role="researcher",
                           verified=True, approved=True)
    return headers


@pytest.fixture()
def admin(make_user):
    headers, _ = make_user("review-admin@example.com", role="admin", verified=True)
    return headers


def test_the_first_release_is_not_held(client, pi):
    """Nothing to subtract from."""
    job_id = run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    assert job_state(client, pi, job_id)["status"] == "completed"


def test_a_near_identical_second_release_is_held(client, pi):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    # The same twelve people plus two more: a difference of two.
    second = build_study(client, pi, name="Second", patients=14)
    job_id = run_extract(client, pi, second)

    state = job_state(client, pi, job_id)
    assert state["status"] == "held_for_review"
    assert "held for disclosure review" in state["error_message"]


def test_a_held_extract_produces_no_file(client, pi):
    """The whole point of holding before building rather than after."""
    from api.models import ExtractionJob

    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    job_id = run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        assert job.result_csv is None
        assert job.download_url is None
    assert client.get(f"/api/extraction/jobs/{job_id}/download",
                      headers=pi).status_code == 400


def test_the_held_message_names_no_other_cohort(client, pi):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    job_id = run_extract(client, pi, build_study(client, pi, name="Second", patients=14))
    message = job_state(client, pi, job_id)["error_message"]
    for digit in "0123456789":
        assert digit not in message, f"held message leaks a number: {message}"


def test_a_distant_second_release_is_not_held(client, pi):
    """Ordinary separate work must not be caught."""
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    # Twelve entirely different people.
    second = build_study(client, pi, name="Second", patients=12, offset=12)
    assert job_state(client, pi, run_extract(client, pi, second))["status"] == "completed"


# ---------------------------------------------------------------------------
# The review
# ---------------------------------------------------------------------------

def held_review(client, admin):
    reviews = client.get("/api/admin/release-reviews", headers=admin).json()
    assert reviews, "expected a pending review"
    return reviews[0]


def test_the_reviewer_sees_the_numbers_and_the_shape(client, pi, admin):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    review = held_review(client, admin)
    assert review["subjects_differing"] == 2
    assert review["shape"] == "same researcher, different study"
    assert review["requested_by"] == "pi@example.com"


def test_the_review_list_carries_no_subjects(client, pi, admin):
    """A reviewer decides whether people can be singled out. Not who they are."""
    import json as _json

    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    from api.models import PatientProfile
    with client._session_factory() as db:
        patient_ids = {str(p.id) for p in db.query(PatientProfile).all()}

    body = _json.dumps(client.get("/api/admin/release-reviews", headers=admin).json())
    for patient_id in patient_ids:
        assert patient_id not in body, "review listing leaks a subject id"


def test_approving_releases_the_extract(client, pi, admin):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    job_id = run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    review = held_review(client, admin)
    result = client.post(f"/api/admin/release-reviews/{review['id']}", headers=admin,
                         json={"decision": "approve", "note": "Same PI, refresh"})
    assert result.status_code == 200, result.text
    assert result.json()["job_status"] == "completed"
    assert job_state(client, pi, job_id)["status"] == "completed"
    assert client.get(f"/api/extraction/jobs/{job_id}/download",
                      headers=pi).status_code == 200


def test_declining_refuses_it_and_says_what_to_do(client, pi, admin):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    job_id = run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    review = held_review(client, admin)
    client.post(f"/api/admin/release-reviews/{review['id']}", headers=admin,
                json={"decision": "decline", "note": "Too close to the March extract"})

    state = job_state(client, pi, job_id)
    assert state["status"] == "failed"
    assert "was not released" in state["error_message"]
    assert "Broaden the cohort" in state["error_message"]
    assert client.get(f"/api/extraction/jobs/{job_id}/download",
                      headers=pi).status_code == 400


def test_a_decision_cannot_be_made_twice(client, pi, admin):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    run_extract(client, pi, build_study(client, pi, name="Second", patients=14))

    review = held_review(client, admin)
    client.post(f"/api/admin/release-reviews/{review['id']}", headers=admin,
                json={"decision": "approve"})
    again = client.post(f"/api/admin/release-reviews/{review['id']}", headers=admin,
                        json={"decision": "decline"})
    assert again.status_code == 409


def test_a_researcher_cannot_review_their_own_extract(client, pi):
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    run_extract(client, pi, build_study(client, pi, name="Second", patients=14))
    assert client.get("/api/admin/release-reviews", headers=pi).status_code in (401, 403)


def test_an_approval_does_not_survive_the_people_changing(client, pi, admin):
    """A reviewer approves a set of subjects, not a job name.

    If the cohort moves between the decision and the release, the reviewer
    never saw the people who would go out. Releasing on that approval would
    be a judgement about one group applied to another.
    """
    from api.models import Consent, ExtractedMedicalData, PatientProfile, StudyEnrollment

    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    second = build_study(client, pi, name="Second", patients=14)
    job_id = run_extract(client, pi, second)
    review = held_review(client, admin)

    # One more person enrols after the extract was held.
    with client._session_factory() as db:
        latecomer = PatientProfile()
        db.add(latecomer)
        db.flush()
        db.add_all([
            Consent(patient_id=latecomer.id,
                    consent_type="research_data_sharing", status="active"),
            ExtractedMedicalData(
                patient_id=latecomer.id, connection_id="synthetic",
                data_category="diagnosis", data_type="condition",
                original_year=2021, deidentified_data={"stage": "II"}),
            StudyEnrollment(study_id=second, patient_id=latecomer.id,
                            status="enrolled"),
        ])
        db.commit()

    result = client.post(f"/api/admin/release-reviews/{review['id']}", headers=admin,
                         json={"decision": "approve"})
    assert result.status_code == 200, result.text
    assert result.json()["job_status"] == "held_for_review"

    state = job_state(client, pi, job_id)
    assert state["status"] == "held_for_review"
    assert "changed since it was last reviewed" in state["error_message"]

    # And a fresh review is open for the set that would actually be released.
    pending = client.get("/api/admin/release-reviews", headers=admin).json()
    assert len(pending) == 1
    assert pending[0]["id"] != review["id"]


def test_the_create_response_calls_a_hold_neither_success_nor_failure(client, pi):
    """Either label misleads the person who asked.

    "success" invites them to look for a file that does not exist; "failed"
    tells them their work was rejected when it is waiting on a person.
    """
    run_extract(client, pi, build_study(client, pi, name="First", patients=12))
    second = build_study(client, pi, name="Second", patients=14)
    response = client.post("/api/extraction/create", headers=pi, json={
        "study_id": second, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    body = response.json()
    assert body["success"] is False
    assert body["held_for_review"] is True
    assert body["status"] == "held_for_review"
    assert "held for disclosure review" in body["message"]
    assert body["download_url"] is None
