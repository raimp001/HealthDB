"""Cohort matching against real model rows, at the precision the data has.

Every one of these ran through a SimpleNamespace test double before, and the
double still carried an `original_date` field the model had already lost. The
result was an AttributeError on any date-filtered cohort, in production,
invisible to a green test suite. So these build genuine ExtractedMedicalData
instances: if a column disappears again, they break here first.
"""
from datetime import date

import pytest

from api.cohort_query import CohortCriteria, matching_patient_ids
from api.models import ExtractedMedicalData


def record(patient_id, category="diagnosis", year=2020, **data):
    return ExtractedMedicalData(
        patient_id=patient_id, connection_id="c", data_category=category,
        original_year=year, deidentified_data=data,
    )


def diagnosis(patient_id, year=2020):
    return record(patient_id, year=year, display="AML", code="C92.0")


# ---------------------------------------------------------------------------
# The regression itself
# ---------------------------------------------------------------------------

def test_a_date_filtered_cohort_runs_against_real_rows():
    """This raised AttributeError against the live model."""
    matched = matching_patient_ids(
        [diagnosis("p1", year=2020)],
        CohortCriteria(diagnosis_date_start=date(2019, 1, 1)),
    )
    assert matched == {"p1"}


def test_a_follow_up_filter_runs_against_real_rows():
    """So did this, whenever no follow-up value was recorded."""
    matching_patient_ids([diagnosis("p1")], CohortCriteria(min_follow_up_months=6))


# ---------------------------------------------------------------------------
# Year granularity, stated explicitly
# ---------------------------------------------------------------------------

def test_a_range_starting_mid_year_includes_that_whole_year():
    """The filter cannot be finer than the stored data, and says so."""
    matched = matching_patient_ids(
        [diagnosis("p1", year=2019)],
        CohortCriteria(diagnosis_date_start=date(2019, 6, 1)),
    )
    assert matched == {"p1"}, "a year-granular filter must not drop in-range patients"


def test_a_year_outside_the_range_is_excluded():
    assert matching_patient_ids(
        [diagnosis("p1", year=2018)],
        CohortCriteria(diagnosis_date_start=date(2019, 1, 1)),
    ) == set()


def test_the_end_of_a_range_includes_its_final_year():
    assert matching_patient_ids(
        [diagnosis("p1", year=2021)],
        CohortCriteria(diagnosis_date_end=date(2021, 3, 1)),
    ) == {"p1"}


def test_a_record_with_no_year_does_not_satisfy_a_date_range():
    """A missing value never establishes an inclusion."""
    assert matching_patient_ids(
        [record("p1", display="AML", code="C92.0", year=None)],
        CohortCriteria(diagnosis_date_start=date(2019, 1, 1)),
    ) == set()


# ---------------------------------------------------------------------------
# Derived follow-up is a lower bound, never an estimate
# ---------------------------------------------------------------------------

def test_recorded_follow_up_months_are_used_directly():
    rows = [diagnosis("p1"), record("p1", category="outcome", follow_up_months=24)]
    assert matching_patient_ids(rows, CohortCriteria(min_follow_up_months=24)) == {"p1"}


def test_derived_follow_up_uses_the_minimum_the_years_allow():
    """2018 and 2021 could be as little as 24 months apart, so 24 is the claim.

    Reporting the midpoint (36) would invent precision the year truncation
    deliberately destroyed and would over-include at the filter boundary.
    """
    rows = [diagnosis("p1", year=2018), diagnosis("p1", year=2021)]
    assert matching_patient_ids(rows, CohortCriteria(min_follow_up_months=24)) == {"p1"}
    assert matching_patient_ids(rows, CohortCriteria(min_follow_up_months=25)) == set()


def test_records_in_one_year_derive_no_follow_up():
    """Two records in 2020 may be a day apart. The floor is zero, not twelve."""
    rows = [diagnosis("p1", year=2020), diagnosis("p1", year=2020)]
    assert matching_patient_ids(rows, CohortCriteria(min_follow_up_months=1)) == set()


def test_a_single_record_derives_no_follow_up():
    assert matching_patient_ids(
        [diagnosis("p1", year=2020)], CohortCriteria(min_follow_up_months=1)
    ) == set()


# ---------------------------------------------------------------------------
# The double and the model must agree
# ---------------------------------------------------------------------------

def test_the_demo_fixtures_carry_the_models_date_field():
    """The public demo builds namespaces by hand; they must not drift either."""
    from api.demo import demo_records

    for row in demo_records():
        assert hasattr(row, "original_year")
        assert not hasattr(row, "original_date")


def test_the_demo_cohort_still_evaluates_a_date_range():
    from api.demo import demo_records

    matched = matching_patient_ids(
        demo_records(), CohortCriteria(diagnosis_date_start=date(2024, 1, 1))
    )
    assert len(matched) == 24
