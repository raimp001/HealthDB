"""What a researcher actually receives in the file, and what it means.

The fifth column of the extract has been wrong twice, in the same way both
times: it looked like a per-record measurement and was a constant.

First it was `quality_score`, written as 100.0 at import by an assignment
statement. Then, measuring the exported projection against everything a
record of that kind could hold, it became the same number on every row —
because what the projection contains is decided by the researcher's variable
selection, not by the patient.

A quality signal is something you filter or weight by. A constant one invites
a decision and gives it nothing to stand on, so these tests require the column
to vary with the record and to describe only what is in the file.
"""
import csv
import io

import pytest


def build(client, headers, *, patients, missing_year=0):
    """An approved study where `missing_year` subjects carry no diagnosis year."""
    from api.models import (Consent, ExtractedMedicalData, PatientProfile,
                            RegulatorySubmission, StudyEnrollment)

    study_id = client.post("/api/researcher/studies", headers=headers,
                           json={"name": "Column study"}).json()["id"]
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id=study_id, document_type="irb_protocol",
                                 status="approved"),
            RegulatorySubmission(study_id=study_id, document_type="dua",
                                 status="signed"),
        ])
        for index in range(patients):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            payload = {"display": "Acute myeloid leukemia"}
            if index >= missing_year:
                payload["diagnosis_year"] = 2021
            db.add_all([
                Consent(patient_id=patient.id,
                        consent_type="research_data_sharing", status="active"),
                StudyEnrollment(study_id=study_id, patient_id=patient.id,
                                status="enrolled"),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="synthetic",
                    data_category="diagnosis", data_type="condition",
                    original_year=2021, deidentified_data=payload),
            ])
        db.commit()
    return study_id


def extract(client, headers, study_id, variables):
    response = client.post("/api/extraction/create", headers=headers, json={
        "study_id": study_id, "variables": variables,
        "output_format": "csv", "deidentification_level": "limited_dataset",
    })
    assert response.status_code == 200, response.text
    job_id = response.json()["job_id"]

    from api.models import ExtractionJob
    with client._session_factory() as db:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).one()
        assert job.status == "completed", job.error_message
        return list(csv.reader(io.StringIO(job.result_csv)))


@pytest.fixture()
def researcher(client, make_user, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "MIN_EXPORT_K", 11)
    headers, _ = make_user("columns@example.com", role="researcher",
                           verified=True, approved=True)
    return headers


def test_the_header_names_what_the_column_measures(client, researcher):
    rows = extract(client, researcher, build(client, researcher, patients=12),
                   ["diagnosis.display", "diagnosis.diagnosis_year"])
    assert rows[0] == ["patient_pseudonym", "data_category", "data_type",
                       "year", "variables_present_pct", "data_json"]
    # The two names it has had, both of which promised more than it measured.
    assert "quality_score" not in rows[0]
    assert "completeness_pct" not in rows[0]


def test_the_column_varies_with_the_record(client, researcher):
    """The defect, twice over: a column that was the same on every row."""
    study_id = build(client, researcher, patients=12, missing_year=1)
    rows = extract(client, researcher, study_id,
                   ["diagnosis.display", "diagnosis.diagnosis_year"])
    column = rows[0].index("variables_present_pct")
    values = sorted({row[column] for row in rows[1:]})
    assert values == ["100.0", "50.0"], values


def test_a_row_carrying_every_requested_variable_reads_full(client, researcher):
    rows = extract(client, researcher, build(client, researcher, patients=12),
                   ["diagnosis.display", "diagnosis.diagnosis_year"])
    column = rows[0].index("variables_present_pct")
    assert {row[column] for row in rows[1:]} == {"100.0"}


def test_the_number_is_scored_against_the_request_not_the_record(client, researcher):
    """Asking for one variable and getting it is 100%, not 25%.

    Scoring against everything a diagnosis could hold would mark a row down
    for fields the researcher never asked for — and those fields are not in
    the file, so the number would be describing withheld data.
    """
    rows = extract(client, researcher, build(client, researcher, patients=12),
                   ["diagnosis.display"])
    column = rows[0].index("variables_present_pct")
    assert {row[column] for row in rows[1:]} == {"100.0"}


def test_the_file_says_nothing_about_fields_that_were_not_released(client, researcher):
    """This file is the disclosure boundary.

    A number derived from fields outside it would be a channel about data the
    researcher was not given.
    """
    study_id = build(client, researcher, patients=12)
    rows = extract(client, researcher, study_id, ["diagnosis.display"])
    for row in rows[1:]:
        assert "diagnosis_year" not in row[-1]
        assert "2021" not in row[-1]
