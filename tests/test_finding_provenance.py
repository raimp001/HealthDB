"""A finding belongs to the people whose data was actually in it.

The contribution chain used to claim a finding for anyone enrolled in the
study that published it. Joining a study is not the same as being in the
extract a finding came from: someone can enrol after the data was drawn, be
filtered out by the cohort, or sit outside a release blocked on disclosure
risk. All of them were told their records had produced the finding.

That broke the chain module's own rule — it counts nothing it cannot show —
and it broke it in the most tempting direction, by being generous. Telling
someone their data mattered when it did not is not a kindness.
"""
from datetime import datetime

import pytest

from api.contribution import build_contribution


def stage(record, key):
    return next(s for s in record["stages"] if s["key"] == key)


@pytest.fixture()
def study(client, make_user):
    """A study with one release, and a participant who was in it."""
    from api.models import (DataRelease, PatientProfile, Study, StudyEnrollment)

    headers, researcher_id = make_user("fp-pi@example.com", role="researcher",
                                       verified=True, approved=True)
    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": "Finding provenance"}).json()["id"]

    with client._session_factory() as db:
        inside = PatientProfile()
        outside = PatientProfile()
        db.add_all([inside, outside])
        db.flush()
        inside_id, outside_id = str(inside.id), str(outside.id)
        db.add_all([
            StudyEnrollment(study_id=study_id, patient_id=inside_id, status="enrolled"),
            StudyEnrollment(study_id=study_id, patient_id=outside_id, status="enrolled"),
            DataRelease(job_id="j1", study_id=study_id, manifest={},
                        manifest_digest="m1", content_digest="digest-one",
                        subject_count=1, record_count=1,
                        subject_ids=[inside_id], released_at=datetime.utcnow()),
        ])
        db.commit()
        release_id = str(db.query(DataRelease).filter(
            DataRelease.job_id == "j1").one().id)

    return {"headers": headers, "study_id": study_id, "release_id": release_id,
            "inside": inside_id, "outside": outside_id}


SUMMARY = ("Across the participants in this study the combination regimen was "
           "associated with a longer remission than the standard one. These are "
           "group averages and individual results varied considerably, so this "
           "does not predict what will happen for any one person.")


def publish(client, study, **overrides):
    body = {"title": "What we found", "plain_language_summary": SUMMARY}
    body.update(overrides)
    return client.post(f"/api/researcher/studies/{study['study_id']}/results",
                       headers=study["headers"], json=body)


# ---------------------------------------------------------------------------
# The overclaim
# ---------------------------------------------------------------------------

def test_a_finding_counts_for_someone_who_was_in_its_release(client, study):
    assert publish(client, study, release_id=study["release_id"]).status_code == 200

    with client._session_factory() as db:
        published = stage(build_contribution(db, study["inside"]), "published")

    assert published["reached"] is True
    assert "1 finding from data including yours" in published["headline"]
    assert published["items"][0]["dataset_recorded"] is True


def test_it_does_not_count_for_someone_the_release_did_not_carry(client, study):
    """Enrolled in the study, absent from the extract. Not their finding."""
    publish(client, study, release_id=study["release_id"])

    with client._session_factory() as db:
        published = stage(build_contribution(db, study["outside"]), "published")

    assert published["reached"] is False
    assert "No findings published from your records" in published["headline"]
    assert published["items"] == []


def test_the_reason_names_the_release_not_the_study(client, study):
    publish(client, study, release_id=study["release_id"])

    with client._session_factory() as db:
        published = stage(build_contribution(db, study["outside"]), "published")

    assert "release containing your records" in published["blocked_because"]


# ---------------------------------------------------------------------------
# A finding that cites nothing
# ---------------------------------------------------------------------------

def test_an_unlinked_finding_is_shown_but_not_claimed(client, study):
    """Hiding it would be its own distortion; claiming it would be a lie."""
    assert publish(client, study).status_code == 200

    with client._session_factory() as db:
        published = stage(build_contribution(db, study["inside"]), "published")

    assert published["reached"] is False, "an unlinked finding is not proof"
    assert published["items"][0]["dataset_recorded"] is False
    assert "did not record which dataset" in published["detail"]
    assert "not something this can tell you" in published["detail"]


def test_an_unlinked_finding_does_not_inflate_the_count(client, study):
    publish(client, study)
    publish(client, study, release_id=study["release_id"])

    with client._session_factory() as db:
        published = stage(build_contribution(db, study["inside"]), "published")

    assert "1 finding from data including yours" in published["headline"]
    assert len(published["items"]) == 2, "both are listed, only one is counted"


# ---------------------------------------------------------------------------
# Citing a dataset
# ---------------------------------------------------------------------------

def test_publishing_returns_the_dataset_digest(client, study):
    """So a finding can be reproduced against the exact bytes behind it."""
    body = publish(client, study, release_id=study["release_id"]).json()
    assert body["release_id"] == study["release_id"]
    assert body["dataset_digest"] == "digest-one"


def test_publishing_without_a_release_says_so_rather_than_guessing(client, study):
    body = publish(client, study).json()
    assert body["release_id"] is None
    assert body["dataset_digest"] is None


def test_a_release_from_another_study_cannot_be_cited(client, study, make_user):
    """Otherwise a finding could borrow evidence it has no claim to."""
    from api.models import DataRelease, Study

    other_headers, other_id = make_user("fp-other@example.com", role="researcher",
                                        verified=True, approved=True)
    other_study = client.post("/api/researcher/studies", headers=other_headers,
                              json={"name": "Someone else"}).json()["id"]
    with client._session_factory() as db:
        db.add(DataRelease(job_id="j2", study_id=other_study, manifest={},
                           manifest_digest="m2", content_digest="digest-two",
                           subject_count=1, record_count=1, subject_ids=[]))
        db.commit()
        foreign = str(db.query(DataRelease).filter(DataRelease.job_id == "j2").one().id)

    assert publish(client, study, release_id=foreign).status_code == 404


def test_a_made_up_release_id_is_refused(client, study):
    assert publish(client, study,
                   release_id="00000000-0000-0000-0000-000000000000").status_code == 404


# ---------------------------------------------------------------------------
# The participant still sees the finding itself
# ---------------------------------------------------------------------------

def test_a_participant_still_reads_findings_from_their_study(client, study, make_user):
    """Provenance decides what the chain claims, not what a person may read."""
    from api.models import PatientProfile, StudyEnrollment

    patient_headers, user_id = make_user("fp-reader@example.com", role="patient")
    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id).one()
        db.add(StudyEnrollment(study_id=study["study_id"],
                               patient_id=str(profile.id), status="enrolled"))
        db.commit()

    publish(client, study, release_id=study["release_id"])
    results = client.get("/api/patient/study-results", headers=patient_headers).json()
    assert len(results) == 1
    assert results[0]["title"] == "What we found"
