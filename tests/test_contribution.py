"""The contribution record replaces the points balance.

Most of these are about the states nobody designs for: the person who
contributed and whose data was never used, the person who joined a study that
published nothing, the person who revoked. Those are the common cases, and
they are where a platform either keeps faith with someone or quietly files
them.

So the assertions are mostly about restraint — that nothing is inflated, that
no stage claims to have happened when it did not, and that the copy never
implies a finding is coming.
"""
from datetime import datetime

import pytest

from api.contribution import STAGES, build_contribution


@pytest.fixture()
def db(client):
    session = client._session_factory()
    yield session
    session.close()


def make_patient(db, *, consented=True):
    from api.models import Consent, PatientProfile

    profile = PatientProfile()
    db.add(profile)
    db.flush()
    if consented:
        db.add(Consent(patient_id=profile.id,
                       consent_type="research_data_sharing", status="active"))
    db.commit()
    return str(profile.id)


def add_records(db, patient_id, years=(2019, 2021), category="diagnosis"):
    from api.models import ExtractedMedicalData

    for year in years:
        db.add(ExtractedMedicalData(
            patient_id=patient_id, connection_id="synthetic",
            data_category=category, original_year=year,
            deidentified_data={"display": "AML"}))
    db.commit()


def stage(record, key):
    return next(s for s in record["stages"] if s["key"] == key)


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------

def test_the_chain_is_always_reported_in_full(db):
    """Every stage appears, including the ones that did not happen.

    Hiding unreached stages would turn the record into a highlight reel.
    """
    record = build_contribution(db, make_patient(db))
    assert [s["key"] for s in record["stages"]] == list(STAGES)


def test_there_is_no_score_anywhere_in_the_record(db):
    """No points, no tier, no percentage standing in for a person."""
    import json

    patient = make_patient(db)
    add_records(db, patient)
    serialized = json.dumps(build_contribution(db, patient)).lower()
    for banned in ("points", "score", "tier", "level", "rank", "balance"):
        assert banned not in serialized, f"the record leaks a {banned}"


# ---------------------------------------------------------------------------
# The zero state — the screen most people will see
# ---------------------------------------------------------------------------

def test_a_new_contributor_sees_an_honest_empty_record(db):
    record = build_contribution(db, make_patient(db))
    assert record["furthest_stage"] is None
    assert all(not s["reached"] for s in record["stages"])
    assert "Nothing has been contributed" in record["summary"]


def test_someone_who_contributed_and_was_never_used_is_not_told_it_is_coming(db):
    """The most common outcome. It must read as a kept promise, not a wait."""
    patient = make_patient(db)
    add_records(db, patient)
    record = build_contribution(db, patient)

    assert record["furthest_stage"] == "contributed"
    assert "No researcher has drawn on them yet" in record["summary"]

    # Nothing anywhere may promise a future finding.
    import json
    text = json.dumps(record).lower()
    for promise in ("coming soon", "will be published", "you will receive",
                    "check back", "stay tuned"):
        assert promise not in text, f"the record promises: {promise}"


def test_an_unreached_stage_says_why_and_does_not_blame_the_contributor(db):
    patient = make_patient(db)
    add_records(db, patient)
    record = build_contribution(db, patient)

    for key in ("searched", "enrolled", "released", "published"):
        blocked = stage(record, key)["blocked_because"]
        assert blocked, f"{key} must say why it has not happened"
        # The chain stops for institutional reasons, never the person's.
        for blame in ("your data was not", "insufficient", "not good enough",
                      "you did not", "you failed"):
            assert blame not in blocked.lower()


def test_the_published_stage_is_candid_that_most_research_publishes_nothing(db):
    patient = make_patient(db)
    add_records(db, patient)
    detail = stage(build_contribution(db, patient), "published")["detail"]
    assert "Most research does not reach a published finding" in detail


# ---------------------------------------------------------------------------
# Stages actually reached
# ---------------------------------------------------------------------------

def test_contributed_reports_categories_and_the_year_span(db):
    patient = make_patient(db)
    add_records(db, patient, years=(2019, 2021))
    contributed = stage(build_contribution(db, patient), "contributed")

    assert contributed["reached"] is True
    assert "2 records contributed" in contributed["headline"]
    assert "2019–2021" in contributed["detail"]
    # The record must restate the privacy guarantee where it is relevant.
    assert "never a month or a day" in contributed["detail"]


def test_being_counted_in_a_feasibility_search_is_reported_as_contribution(db):
    """Data that never leaves still shapes what researchers know to ask."""
    from api.models import CohortQueryLog, User

    patient = make_patient(db)
    add_records(db, patient)
    user = User(email="searcher@example.com", password_hash="x", name="R",
                user_type="researcher")
    db.add(user)
    db.flush()
    db.add(CohortQueryLog(user_id=user.id, patient_set=[patient], patient_count=1))
    db.commit()

    searched = stage(build_contribution(db, patient), "searched")
    assert searched["reached"] is True
    assert "1 recent feasibility search" in searched["headline"]
    assert "No one saw your data" in searched["detail"]


def test_a_search_that_did_not_include_this_person_is_not_counted(db):
    from api.models import CohortQueryLog, User

    patient = make_patient(db)
    other = make_patient(db)
    user = User(email="searcher2@example.com", password_hash="x", name="R",
                user_type="researcher")
    db.add(user)
    db.flush()
    db.add(CohortQueryLog(user_id=user.id, patient_set=[other], patient_count=1))
    db.commit()

    assert stage(build_contribution(db, patient), "searched")["reached"] is False


def test_enrolment_lists_the_studies_by_name(db):
    from api.models import Study, StudyEnrollment, User

    patient = make_patient(db)
    owner = User(email="pi-contrib@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Remission duration in AML", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add(StudyEnrollment(study_id=study.id, patient_id=patient, status="enrolled"))
    db.commit()

    enrolled = stage(build_contribution(db, patient), "enrolled")
    assert enrolled["reached"] is True
    assert enrolled["items"] == [{"study_name": "Remission duration in AML"}]


def test_a_withdrawn_enrolment_does_not_count_as_joined(db):
    from api.models import Study, StudyEnrollment, User

    patient = make_patient(db)
    owner = User(email="pi-withdrawn@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Left study", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add(StudyEnrollment(study_id=study.id, patient_id=patient, status="withdrawn"))
    db.commit()

    assert stage(build_contribution(db, patient), "enrolled")["reached"] is False


def test_a_release_is_shown_with_its_fingerprint_and_download_state(db):
    from api.models import DataRelease, Study, User

    patient = make_patient(db)
    owner = User(email="pi-release@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Released study", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add(DataRelease(job_id="j", study_id=str(study.id), manifest={},
                       manifest_digest="m", content_digest="abc123",
                       subject_count=11, record_count=11,
                       subject_ids=[patient], download_count=1,
                       first_downloaded_at=datetime.utcnow()))
    db.commit()

    released = stage(build_contribution(db, patient), "released")
    assert released["reached"] is True
    assert released["items"][0]["content_digest"] == "abc123"
    assert released["items"][0]["downloaded"] is True


def test_a_release_that_did_not_carry_this_person_is_not_shown(db):
    from api.models import DataRelease, Study, User

    patient = make_patient(db)
    owner = User(email="pi-other@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Someone else's study", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add(DataRelease(job_id="j2", study_id=str(study.id), manifest={},
                       manifest_digest="m", content_digest="zzz",
                       subject_count=11, record_count=11,
                       subject_ids=["a-different-person"]))
    db.commit()

    assert stage(build_contribution(db, patient), "released")["reached"] is False


def test_a_published_finding_is_the_furthest_stage(db):
    from api.models import Study, StudyEnrollment, StudyResult, User

    patient = make_patient(db)
    owner = User(email="pi-published@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Published study", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add_all([
        StudyEnrollment(study_id=study.id, patient_id=patient, status="enrolled"),
        StudyResult(study_id=str(study.id), title="What we found",
                    plain_language_summary="x" * 200),
    ])
    db.commit()

    record = build_contribution(db, patient)
    assert record["furthest_stage"] == "published"
    assert stage(record, "published")["items"][0]["title"] == "What we found"


def test_a_finding_from_a_study_this_person_did_not_join_is_not_shown(db):
    from api.models import Study, StudyResult, User

    patient = make_patient(db)
    owner = User(email="pi-unjoined@example.com", password_hash="x", name="PI",
                 user_type="researcher")
    db.add(owner)
    db.flush()
    study = Study(name="Unrelated study", user_id=owner.id)
    db.add(study)
    db.flush()
    db.add(StudyResult(study_id=str(study.id), title="Not yours",
                       plain_language_summary="x" * 200))
    db.commit()

    assert stage(build_contribution(db, patient), "published")["reached"] is False


# ---------------------------------------------------------------------------
# Through the API
# ---------------------------------------------------------------------------

def test_a_patient_sees_only_their_own_chain(client, make_user):
    from api.models import PatientProfile

    headers, user_id = make_user("contrib@example.com", role="patient")
    with client._session_factory() as session:
        mine = session.query(PatientProfile).filter(
            PatientProfile.user_id == user_id).one()
        add_records(session, str(mine.id))
        # Somebody else's records must not appear in my chain.
        theirs = PatientProfile()
        session.add(theirs)
        session.flush()
        add_records(session, str(theirs.id), years=(2001, 2002, 2003))

    response = client.get("/api/patient/contribution", headers=headers)
    assert response.status_code == 200, response.text
    contributed = next(s for s in response.json()["stages"]
                       if s["key"] == "contributed")
    assert "2 records contributed" in contributed["headline"]


def test_a_researcher_cannot_read_a_contribution_record(client, approved_researcher):
    assert client.get("/api/patient/contribution",
                      headers=approved_researcher).status_code in (401, 403)


def test_the_route_requires_a_session(client):
    assert client.get("/api/patient/contribution").status_code in (401, 403)
