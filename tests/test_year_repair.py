"""The year a record states must be the year a cohort can find it by.

A patient uploads their history, the diagnosis year is truncated to a year
for Safe Harbor, and then — in the bug these tests exist to prevent — the
year is dropped on the way into the column researchers actually query. The
record is stored, counted, and consented, and matches no date-scoped cohort
at all. Nobody is told, because a null year looks exactly like a record whose
source carried no date.
"""
from types import SimpleNamespace

import pytest

from api.year_repair import repairable, survey, year_in_payload


def row(year=None, data=None):
    return SimpleNamespace(original_year=year, deidentified_data=data or {})


# ---------------------------------------------------------------------------
# Reading the year a record already carries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload,expected", [
    ({"diagnosis_year": 2020}, 2020),
    ({"year": 2019}, 2019),
    ({"start_year": 2015}, 2015),
    ({"death_year": 2023}, 2023),
    ({"display": "AML", "diagnosis_year": 2021}, 2021),
])
def test_the_year_is_read_from_wherever_the_parser_put_it(payload, expected):
    assert year_in_payload(payload) == expected


def test_a_payload_with_no_year_yields_nothing_to_copy():
    """Records really do exist with no date. Those stay null, honestly."""
    assert year_in_payload({"display": "AML", "stage": "III"}) is None
    assert year_in_payload({"age_band": "60-69"}) is None


def test_two_disagreeing_years_are_refused_rather_than_picked_between():
    """Picking one would bury the fact that something upstream is wrong."""
    assert year_in_payload({"year": 2019, "death_year": 2023}) is None


def test_two_agreeing_years_are_not_a_disagreement():
    assert year_in_payload({"year": 2019, "diagnosis_year": 2019}) == 2019


@pytest.mark.parametrize("value", [None, "2020", True, 20.5, [], {"year": 1}])
def test_a_year_that_is_not_a_whole_number_is_not_a_year(value):
    assert year_in_payload({"year": value}) is None


def test_a_number_that_cannot_be_a_year_is_not_read_as_one():
    assert year_in_payload({"quality_score": 95}) is None
    assert year_in_payload({"year": 12}) is None


# ---------------------------------------------------------------------------
# What may be written
# ---------------------------------------------------------------------------

def test_a_row_missing_its_year_is_repairable():
    assert repairable(row(None, {"diagnosis_year": 2020})) == 2020


def test_a_row_that_already_has_a_year_is_never_touched():
    """Filling gaps is a repair. Rewriting stored values is a corruption."""
    assert repairable(row(2020, {"diagnosis_year": 1999})) is None


def test_a_row_with_no_year_anywhere_stays_as_it_is():
    assert repairable(row(None, {"display": "AML"})) is None


def test_the_survey_separates_what_can_be_fixed_from_what_cannot():
    state = survey([
        row(2020, {"diagnosis_year": 2020}),      # fine
        row(None, {"diagnosis_year": 2021}),      # repairable
        row(None, {"year": 2022}),                # repairable
        row(None, {"display": "AML"}),            # genuinely undated
    ])
    assert state["rows_without_a_year"] == 3
    assert state["rows_repairable"] == 2
    assert state["rows_with_no_year_recorded_anywhere"] == 1


# ---------------------------------------------------------------------------
# The invariant that would have caught this
# ---------------------------------------------------------------------------

@pytest.fixture()
def contributor(client, make_user):
    """A real patient profile id; these rows belong to someone."""
    from api.models import PatientProfile

    _, user_id = make_user("year-contributor@example.com", role="patient")
    with client._session_factory() as db:
        return db.query(PatientProfile).filter(
            PatientProfile.user_id == user_id).one().id


def stored(patient_id, **kwargs):
    from api.models import ExtractedMedicalData
    return ExtractedMedicalData(patient_id=patient_id, connection_id="synthetic",
                                **kwargs)


def test_the_audit_fails_when_a_stated_year_is_not_stored(client, contributor):
    from api.models import ExtractedMedicalData
    from api.self_audit import check_stored_years_were_not_dropped

    with client._session_factory() as db:
        assert check_stored_years_were_not_dropped(db).passed

        db.add(stored(contributor, data_category="diagnosis",
                      data_type="condition", original_year=None,
                      deidentified_data={"display": "AML",
                                         "diagnosis_year": 2021}))
        db.commit()

        finding = check_stored_years_were_not_dropped(db)
        assert not finding.passed
        assert finding.severity == "blocker"
        assert finding.count == 1


def test_the_audit_does_not_fault_a_record_that_never_had_a_date(client, contributor):
    """Missing is not the same as dropped, and conflating them cries wolf."""
    from api.models import ExtractedMedicalData
    from api.self_audit import check_stored_years_were_not_dropped

    with client._session_factory() as db:
        db.add(stored(contributor, data_category="demographics",
                      data_type="patient", original_year=None,
                      deidentified_data={"age_band": "60-69"}))
        db.commit()
        assert check_stored_years_were_not_dropped(db).passed


# ---------------------------------------------------------------------------
# Through the admin surface
# ---------------------------------------------------------------------------

@pytest.fixture()
def admin(make_user):
    headers, _ = make_user("year-admin@example.com", role="admin", verified=True)
    return headers


def _damaged(client, patient_id):
    """One record that lost its year, one that genuinely never had one."""
    with client._session_factory() as db:
        db.add_all([
            stored(patient_id, data_category="diagnosis", data_type="condition",
                   original_year=None,
                   deidentified_data={"display": "AML", "diagnosis_year": 2021}),
            stored(patient_id, data_category="demographics", data_type="patient",
                   original_year=None,
                   deidentified_data={"age_band": "60-69"}),
        ])
        db.commit()


def test_the_preview_reads_only(client, admin, contributor):
    _damaged(client, contributor)
    body = client.get("/api/admin/maintenance/missing-years", headers=admin).json()
    assert body["rows_repairable"] == 1
    assert body["rows_with_no_year_recorded_anywhere"] == 1

    from api.models import ExtractedMedicalData
    with client._session_factory() as db:
        assert db.query(ExtractedMedicalData).filter(
            ExtractedMedicalData.original_year.isnot(None)).count() == 0


def test_the_repair_restores_the_year_and_leaves_the_undated_alone(client, admin, contributor):
    from api.models import ExtractedMedicalData

    _damaged(client, contributor)
    body = client.post("/api/admin/maintenance/missing-years", headers=admin).json()
    assert body["applied"] is True
    assert body["rows_repaired"] == 1
    assert body["rows_repairable"] == 0

    with client._session_factory() as db:
        years = sorted(
            (r.data_category, r.original_year)
            for r in db.query(ExtractedMedicalData).all())
    assert years == [("demographics", None), ("diagnosis", 2021)]


def test_repairing_twice_changes_nothing_the_second_time(client, admin, contributor):
    _damaged(client, contributor)
    client.post("/api/admin/maintenance/missing-years", headers=admin)
    body = client.post("/api/admin/maintenance/missing-years", headers=admin).json()
    assert body["applied"] is False
    assert body["rows_repaired"] == 0


def test_a_non_admin_cannot_run_it(client, make_user):
    headers, _ = make_user("year-patient@example.com", role="patient")
    assert client.post("/api/admin/maintenance/missing-years",
                       headers=headers).status_code in (401, 403)
    assert client.get("/api/admin/maintenance/missing-years",
                      headers=headers).status_code in (401, 403)
