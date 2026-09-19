"""Refuse a record rather than store one nobody can trust.

A malformed value stored "just in case" does not sit there harmlessly. It is
counted in a feasibility search, drawn into a cohort, and averaged into a
finding — so the contributor's data starts making the science worse, which is
the opposite of why they gave it.

The other half of these tests is about restraint: rejecting values that
*cannot* be true, never values that are merely unusual. Rare is what a lot of
cancer research is looking for, and a platform that quietly discards outliers
has decided what counts as a real patient.
"""
from datetime import datetime

import pytest

from api.ingest_validation import (MAX_PLAUSIBLE_AGE, check_record,
                                   describe_rejections, partition)


def record(data=None, *, year=2020, category="diagnosis", type_="condition"):
    return {
        "data_category": category,
        "data_type": type_,
        "original_year": year,
        "data": {"display": "AML"} if data is None else data,
    }


# ---------------------------------------------------------------------------
# What cannot be true
# ---------------------------------------------------------------------------

def test_a_sound_record_is_kept():
    assert check_record(record()) is None


def test_an_entry_with_no_content_is_refused():
    """Storing it would inflate every count that includes it, carrying nothing."""
    assert "no readable clinical information" in check_record(record({}))
    assert check_record(record({"display": "", "stage": None})) is not None


def test_a_year_before_modern_records_is_refused():
    reason = check_record(record(year=1782))
    assert reason and "1782" in reason


def test_a_future_year_is_refused_as_a_typo_not_a_prediction():
    future = datetime.utcnow().year + 1
    reason = check_record(record(year=future))
    assert reason and "in the future" in reason


def test_a_year_that_is_not_a_year_is_refused():
    assert "could not be read as a year" in check_record(record(year="last Tuesday"))


def test_an_age_beyond_a_human_lifespan_is_refused():
    reason = check_record(record({"display": "AML", "age": MAX_PLAUSIBLE_AGE + 40}))
    assert reason and "beyond a human" in reason


def test_a_negative_age_is_refused():
    assert "negative" in check_record(record({"display": "AML", "age": -4}))


def test_an_implausible_bound_inside_an_age_band_is_refused():
    """A band is two numbers; both have to be believable."""
    assert check_record(record({"display": "AML", "age_band": "70-900"})) is not None


# ---------------------------------------------------------------------------
# What is merely unusual, and must be kept
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("data", [
    {"display": "AML", "age": 0},                       # a newborn
    {"display": "AML", "age": MAX_PLAUSIBLE_AGE},       # the oldest plausible
    {"display": "AML", "age_band": "90+"},              # Safe Harbor's own band
    {"display": "Extremely rare unnamed sarcoma"},      # a rare disease
    {"display": "AML", "stage": "unknown"},             # missing is not wrong
    {"display": "AML", "quality_score": 0},             # a real zero
])
def test_unusual_but_possible_records_are_kept(data):
    """Rare is what a lot of cancer research is looking for."""
    assert check_record(record(data)) is None


def test_a_record_with_no_year_is_kept():
    """A missing date is not an impossible one."""
    assert check_record(record(year=None)) is None


def test_the_earliest_plausible_year_itself_is_kept():
    assert check_record(record(year=1900)) is None


def test_the_current_year_is_kept():
    assert check_record(record(year=datetime.utcnow().year)) is None


# ---------------------------------------------------------------------------
# One bad entry must not cost the good ones
# ---------------------------------------------------------------------------

def test_a_bundle_keeps_its_sound_records_and_refuses_the_rest():
    """Refusing the whole upload teaches people not to bother."""
    accepted, rejected = partition([
        record(), record(year=1500), record(), record({}),
    ])
    assert len(accepted) == 2
    assert len(rejected) == 2


def test_order_is_preserved_so_a_person_can_find_the_entry():
    accepted, rejected = partition([
        record(type_="first"), record(type_="bad", year=1500), record(type_="third"),
    ])
    assert [r["data_type"] for r in accepted] == ["first", "third"]
    assert rejected[0][0]["data_type"] == "bad"


def test_nothing_is_rejected_from_a_clean_bundle():
    accepted, rejected = partition([record(), record()])
    assert len(accepted) == 2 and rejected == []


# ---------------------------------------------------------------------------
# What the contributor is told
# ---------------------------------------------------------------------------

def test_the_explanation_names_the_entry_and_the_reason():
    _, rejected = partition([record(category="diagnosis", type_="condition", year=1500)])
    described = describe_rejections(rejected)[0]
    assert described["category"] == "diagnosis"
    assert described["type"] == "condition"
    assert described["year"] == 1500
    assert "1500" in described["reason"]


def test_the_explanation_carries_no_parser_internals():
    """Someone reading their own health record should recognise this."""
    _, rejected = partition([record({}), record(year=1500),
                             record({"display": "AML", "age": 400})])
    for described in describe_rejections(rejected):
        reason = described["reason"]
        for jargon in ("KeyError", "None", "traceback", "field", "schema",
                       "parse_fhir", "dict", "null"):
            assert jargon not in reason, f"reason leaks internals: {reason}"


# ---------------------------------------------------------------------------
# Through the upload
# ---------------------------------------------------------------------------

@pytest.fixture()
def uploader(client, make_user, monkeypatch):
    """A patient who may actually upload: consent signed, flag on."""
    import api.main as main
    from api.models import Consent, PatientProfile

    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", True)
    headers, user_id = make_user("ingest@example.com", role="patient")
    with client._session_factory() as db:
        profile = db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id).one()
        db.add(Consent(patient_id=profile.id,
                       consent_type="research_data_sharing", status="active"))
        db.commit()
    return headers


def bundle(*resources):
    return {"resourceType": "Bundle",
            "entry": [{"resource": r} for r in resources]}


def test_an_upload_keeps_the_good_and_reports_the_rest(client, uploader):
    from api.models import ExtractedMedicalData

    response = client.post("/api/patient/connections/fhir", headers=uploader, json={
        "source_name": "Test", "source_type": "fhir_api",
        "bundle": bundle(
            {"resourceType": "Condition", "code": {"text": "AML"},
             "onsetDateTime": "2020-05-04"},
            {"resourceType": "Condition", "code": {"text": "CLL"},
             "onsetDateTime": "1782-01-01"},
        ),
    })
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["records_imported"] == 1
    assert body["records_rejected"] == 1
    assert "1782" in body["rejections"][0]["reason"]
    assert "not stored" in body["message"]

    with client._session_factory() as db:
        stored = db.query(ExtractedMedicalData).all()
    assert len(stored) == 1
    assert all(r.original_year != 1782 for r in stored)


def test_a_refused_entry_is_never_written(client, uploader):
    """The whole point of refusing rather than flagging."""
    from api.models import ExtractedMedicalData

    response = client.post("/api/patient/connections/fhir", headers=uploader, json={
        "source_name": "Test", "source_type": "fhir_api",
        "bundle": bundle({"resourceType": "Condition", "code": {"text": "AML"},
                          "onsetDateTime": "1500-01-01"}),
    })
    # Assert the upload actually ran. Without this, an upload refused for some
    # unrelated reason would also store nothing, and this test would pass
    # while proving nothing about quarantine.
    assert response.status_code == 200, response.text
    assert response.json()["records_rejected"] >= 1

    with client._session_factory() as db:
        assert db.query(ExtractedMedicalData).count() == 0


def test_a_clean_upload_says_nothing_about_rejections(client, uploader):
    response = client.post("/api/patient/connections/fhir", headers=uploader, json={
        "source_name": "Test", "source_type": "fhir_api",
        "bundle": bundle({"resourceType": "Condition", "code": {"text": "AML"},
                          "onsetDateTime": "2020-05-04"}),
    })
    body = response.json()
    assert body["records_rejected"] == 0
    assert body["rejections"] == []
    assert "not stored" not in body["message"]
