"""Tell a researcher an extract would be blocked while they can still change it.

The old sequence was: design a cohort, build a study, obtain IRB approval,
negotiate a data-use agreement, request the extract, and only then learn it
cannot be released. Months, to find out something knowable on day one.

The constraint that shapes these tests is that the warning must not become a
counting channel. The extract path returns full measurements — k, class
sizes, subjects at risk — but it sits behind IRB approval and a signed DUA.
Cohort feasibility does not. So the preview is a verdict and a lever, and the
numbers stay where the approvals are.
"""
import pytest

import api.main as main


@pytest.fixture()
def researcher(client, make_user, monkeypatch):
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    headers, _ = make_user("preview@example.com", role="researcher",
                           verified=True, approved=True)
    return headers


def seed(client, subjects, *, years=(2020,)):
    """`subjects` consented patients, each holding the same set of years."""
    from api.models import Consent, ExtractedMedicalData, PatientProfile

    with client._session_factory() as db:
        for _ in range(subjects):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            db.add(Consent(patient_id=patient.id,
                           consent_type="research_data_sharing", status="active"))
            for year in years:
                db.add(ExtractedMedicalData(
                    patient_id=patient.id, connection_id="synthetic",
                    data_category="diagnosis", original_year=year,
                    deidentified_data={"display": "AML", "stage": "II"}))
        db.commit()


def build(client, headers, **criteria):
    response = client.post("/api/cohort/build", headers=headers, json=criteria)
    assert response.status_code == 200, response.text
    return response.json()


def test_a_releasable_cohort_says_so(client, researcher):
    seed(client, 11)
    result = build(client, researcher, cancer_types=["AML"])
    assert result["releasable"] is True
    assert "would pass" in result["releasability_note"]


def test_a_pass_is_not_mistaken_for_an_approval(client, researcher):
    """Clearing the disclosure check is not permission to extract."""
    seed(client, 11)
    note = build(client, researcher, cancer_types=["AML"])["releasability_note"]
    assert "not an approval" in note
    assert "IRB" in note and "DUA" in note


def test_a_cohort_that_would_be_blocked_says_so_and_names_the_lever(client, researcher):
    """One subject with a unique year set makes the whole extract unreleasable."""
    seed(client, 11)
    seed(client, 1, years=(1974,))
    result = build(client, researcher, cancer_types=["AML"])
    assert result["releasable"] is False
    assert "would be blocked" in result["releasability_note"]
    assert "Broadening the criteria" in result["releasability_note"]


def test_the_warning_arrives_before_a_study_exists(client, researcher):
    """The whole point: no study, no IRB, no DUA, and the answer is available."""
    from api.models import Study

    seed(client, 11)
    seed(client, 1, years=(1931,))
    result = build(client, researcher, cancer_types=["AML"])

    assert result["releasable"] is False
    with client._session_factory() as db:
        assert db.query(Study).count() == 0


def test_an_empty_cohort_has_nothing_to_say(client, researcher):
    result = build(client, researcher, cancer_types=["nothing matches this"])
    assert result["releasable"] is None
    assert result["releasability_note"] is None


# ---------------------------------------------------------------------------
# It must not become a way to count small groups
# ---------------------------------------------------------------------------

def test_the_preview_carries_no_measurements(client, researcher):
    """A verdict and a lever. Not k, not class sizes, not subjects at risk."""
    import json
    import re

    seed(client, 11)
    seed(client, 1, years=(1974,))
    result = build(client, researcher, cancer_types=["AML"])

    note = result["releasability_note"]
    assert not re.search(r"\d", note), f"the note leaks a number: {note}"
    for banned in ("k=", "equivalence", "class size", "smallest group"):
        assert banned not in note.lower()

    # And nothing numeric rides along in a neighbouring field.
    payload = json.dumps(result)
    assert "min_k" not in payload
    assert "at_risk" not in payload
    assert "class_size_histogram" not in payload


def test_two_cohorts_differing_by_one_person_give_the_same_note(client, researcher):
    """Otherwise the wording itself would be a counting channel."""
    seed(client, 11)
    first = build(client, researcher, cancer_types=["AML"])
    seed(client, 1, years=(1974,))
    second = build(client, researcher, cancer_types=["AML"], age_max=130)

    if first["releasability_note"] and second["releasability_note"]:
        blocked_notes = {n for n in (first["releasability_note"],
                                     second["releasability_note"])
                         if "blocked" in n}
        # Any two blocked cohorts must read identically.
        assert len(blocked_notes) <= 1


def test_a_suppressed_cohort_reveals_no_releasability_at_all(client, researcher, monkeypatch):
    """Below the cell-size floor the count is withheld; so is everything else."""
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 11)
    seed(client, 3)
    result = build(client, researcher, cancer_types=["AML"])

    assert result["suppressed"] is True
    assert result["releasable"] is None, \
        "a withheld cohort must not answer questions about itself"


def test_the_full_measurements_still_require_the_approvals(client, researcher):
    """The numbers stay behind IRB and DUA, where they always were."""
    seed(client, 11)
    study_id = client.post("/api/researcher/studies", headers=researcher,
                           json={"name": "Preview study"}).json()["id"]

    refused = client.post("/api/extraction/create", headers=researcher, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset"})
    assert refused.status_code == 400
    assert "IRB" in refused.json()["detail"]
