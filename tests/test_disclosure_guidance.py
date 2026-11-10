"""A blocked extract should name the thing that blocked it.

A researcher reaching the export step has designed a cohort, obtained an IRB
approval and signed a data-use agreement. What came back was "Broaden the
cohort or drop identifying variables" — advice with no object. With half a
dozen fields there are many combinations, each one a round trip, and the
people who consented sit in a cohort nobody can use.

The system formed the equivalence classes, so it already knows. These tests
hold two lines: it names the field, and it refuses to help anyone strip a
dataset down to nothing just to get it through.
"""
import pytest

from api.disclosure_guidance import advise, single_removals_that_clear


def rows(n=12, **overrides):
    out = []
    for i in range(n):
        row = {"subject_id": f"p{i}", "original_year": 2020, "sex": "F"}
        for key, values in overrides.items():
            row[key] = values[i % len(values)]
        out.append(row)
    return out


QI = ("original_year", "sex")


# ---------------------------------------------------------------------------
# Naming the lever
# ---------------------------------------------------------------------------

def test_the_single_blocking_variable_is_named():
    data = rows()
    data[0]["original_year"] = 1974          # one outlier year
    found = single_removals_that_clear(data, threshold_k=11,
                                       quasi_identifiers=QI,
                                       collapse_by_subject=True)
    assert [s.field for s in found] == ["original_year"]
    assert found[0].resulting_k == 12


def test_the_message_says_what_removing_it_would_achieve():
    data = rows()
    data[0]["original_year"] = 1974
    message = advise(data, threshold_k=11, quasi_identifiers=QI,
                     collapse_by_subject=True)
    assert "original_year" in message
    assert "would become 12" in message


def test_suggestions_are_ranked_by_the_room_they_leave():
    data = rows(13)
    data[0]["original_year"] = 1974
    data[0]["sex"] = "M"
    found = single_removals_that_clear(data, threshold_k=11,
                                       quasi_identifiers=QI,
                                       collapse_by_subject=True)
    assert [s.resulting_k for s in found] == sorted(
        (s.resulting_k for s in found), reverse=True)


# ---------------------------------------------------------------------------
# What it refuses to suggest
# ---------------------------------------------------------------------------

def test_it_will_not_propose_gutting_the_dataset():
    """No single removal is enough, so the answer is to broaden the cohort.

    Searching for the smallest set of fields whose removal gets an extract
    through is an optimiser against a privacy control, and the researcher
    who follows it ends up without the variables their question needed.
    """
    data = [{"subject_id": f"p{i}", "original_year": 2000 + i,
             "sex": ["F", "M", "X"][i % 3]} for i in range(12)]
    assert single_removals_that_clear(data, threshold_k=11,
                                      quasi_identifiers=QI,
                                      collapse_by_subject=True) == []

    message = advise(data, threshold_k=11, quasi_identifiers=QI,
                     collapse_by_subject=True)
    assert "cohort itself is too narrow" in message
    assert "unlikely to answer the question you asked" in message


def test_it_only_suggests_fields_the_researcher_can_remove():
    """Advice to drop something they cannot deselect cannot be taken."""
    data = rows()
    data[0]["original_year"] = 1974
    message = advise(data, threshold_k=11, quasi_identifiers=QI,
                     requested_fields=["sex"], collapse_by_subject=True)
    assert "original_year" not in message
    assert "cohort itself is too narrow" in message


def test_a_field_no_row_carries_is_never_suggested():
    data = rows()
    data[0]["original_year"] = 1974
    found = single_removals_that_clear(
        data, threshold_k=11,
        quasi_identifiers=("original_year", "sex", "zip3"),
        collapse_by_subject=True)
    assert "zip3" not in [s.field for s in found]


# ---------------------------------------------------------------------------
# What the design-time preview may say
# ---------------------------------------------------------------------------

def test_the_number_free_form_still_names_the_field():
    data = rows()
    data[0]["original_year"] = 1974
    message = advise(data, threshold_k=11, quasi_identifiers=QI,
                     with_numbers=False, collapse_by_subject=True)
    assert "original_year" in message
    for digit in "0123456789":
        assert digit not in message, f"number-free guidance leaked: {message}"


def test_the_fallback_carries_no_numbers_either():
    data = [{"subject_id": f"p{i}", "original_year": 2000 + i} for i in range(12)]
    message = advise(data, threshold_k=11, quasi_identifiers=QI,
                     with_numbers=False, collapse_by_subject=True)
    for digit in "0123456789":
        assert digit not in message


# ---------------------------------------------------------------------------
# Through the export, where the advice has to be takeable
# ---------------------------------------------------------------------------

def build_study(client, headers, *, patients, years):
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            RegulatorySubmission, StudyEnrollment)

    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": "Guidance study"}).json()["id"]
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id,
                                 document_type="irb_protocol", status="approved"),
            RegulatorySubmission(study_id=study_id,
                                 document_type="dua", status="signed"),
        ])
        for index in range(patients):
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
                    data_category="diagnosis", original_year=years[index],
                    deidentified_data={"stage": "II"}),
            ])
        db.commit()
    return study_id


def extract(client, headers, study_id, **extra):
    return client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": ["diagnosis.stage"],
        "output_format": "csv", "deidentification_level": "limited_dataset",
        **extra,
    }).json()


@pytest.fixture()
def researcher(client, make_user, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)
    headers, _ = make_user("guide@example.com", role="researcher",
                           verified=True, approved=True)
    return headers


OUTLIER = [2020] * 11 + [1974]


def test_a_blocked_extract_names_the_variable(client, researcher):
    study_id = build_study(client, researcher, patients=12, years=OUTLIER)
    result = extract(client, researcher, study_id)
    assert result["status"] == "failed"
    assert "original_year" in result["message"]
    assert "Removing any one of these" in result["message"]


def test_the_advice_can_actually_be_taken(client, researcher):
    """The point of naming a lever is that pulling it works."""
    study_id = build_study(client, researcher, patients=12, years=OUTLIER)
    assert extract(client, researcher, study_id)["status"] == "failed"

    released = extract(client, researcher,
                       build_study(client, researcher, patients=12, years=OUTLIER),
                       include_year=False)
    assert released["status"] == "completed", released


def test_declining_the_year_leaves_the_column_blank(client, researcher):
    import csv
    import io

    from api.models import ExtractionJob

    study_id = build_study(client, researcher, patients=12, years=OUTLIER)
    job_id = extract(client, researcher, study_id, include_year=False)["job_id"]

    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        rows_out = list(csv.reader(io.StringIO(job.result_csv)))

    year_column = rows_out[0].index("year")
    assert rows_out[0] == ["patient_pseudonym", "data_category", "data_type",
                           "year", "variables_present_pct", "data_json"]
    assert all(row[year_column] == "" for row in rows_out[1:])
    # And the year that blocked it is nowhere in the file.
    assert "1974" not in job.result_csv


def test_the_year_still_ships_by_default(client, researcher):
    """Nothing is quietly dropped from anyone's export."""
    import csv
    import io

    from api.models import ExtractionJob

    study_id = build_study(client, researcher, patients=12, years=[2020] * 12)
    job_id = extract(client, researcher, study_id)["job_id"]

    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        rows_out = list(csv.reader(io.StringIO(job.result_csv)))

    year_column = rows_out[0].index("year")
    assert all(row[year_column] == "2020" for row in rows_out[1:])
