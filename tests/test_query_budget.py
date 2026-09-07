"""Tests for the differencing defence.

The attack these prevent is not exotic. Ask for a cohort, ask again with one
extra exclusion, subtract. Both answers clear the small-cell floor and the
difference is one person. Everything here is written from the attacker's side:
the assertions are that the attack fails, not that the happy path works.
"""
from types import SimpleNamespace

import pytest

from api.query_budget import (
    DEFAULT_HISTORY_DEPTH,
    find_differencing_risk,
    prune_history,
    recent_history,
)


def prior(query_id, ids):
    return SimpleNamespace(id=query_id, patient_set=list(ids))


def people(n, offset=0):
    return [f"p{i}" for i in range(offset, offset + n)]


# ---------------------------------------------------------------------------
# The metric
# ---------------------------------------------------------------------------

def test_a_cohort_one_person_smaller_is_refused():
    """The canonical attack: 40 patients, then 39."""
    history = [prior("q1", people(40))]
    risk = find_differencing_risk(people(39), history, threshold=11)
    assert risk is not None
    assert risk.difference == 1
    assert "1 patient(s)" in risk.message()


def test_a_cohort_one_person_larger_is_also_refused():
    """Adding a person discloses that person just as subtracting one does."""
    history = [prior("q1", people(40))]
    assert find_differencing_risk(people(41), history, threshold=11) is not None


def test_a_swap_of_one_person_is_refused():
    """Same size, different people. Counting alone would miss this entirely."""
    history = [prior("q1", people(40))]
    swapped = people(39) + ["someone-else"]
    risk = find_differencing_risk(swapped, history, threshold=11)
    assert risk is not None
    assert risk.difference == 2
    assert risk.new_count == risk.prior_count


def test_a_genuinely_different_cohort_is_allowed():
    history = [prior("q1", people(40))]
    assert find_differencing_risk(people(40, offset=100), history, threshold=11) is None


def test_a_difference_exactly_at_the_floor_is_allowed():
    """The floor is the smallest group allowed to be revealed, so it passes."""
    history = [prior("q1", people(40))]
    assert find_differencing_risk(people(29), history, threshold=11) is None


def test_a_difference_one_below_the_floor_is_refused():
    history = [prior("q1", people(40))]
    assert find_differencing_risk(people(30), history, threshold=11) is not None


def test_repeating_the_identical_query_is_allowed():
    """Re-running a query tells the researcher nothing new."""
    history = [prior("q1", people(40))]
    assert find_differencing_risk(people(40), history, threshold=11) is None


def test_every_prior_result_is_checked_not_only_the_last():
    """An attacker would simply interleave an unrelated query."""
    history = [
        prior("recent", people(40, offset=500)),
        prior("older", people(40)),
    ]
    risk = find_differencing_risk(people(39), history, threshold=11)
    assert risk is not None
    assert risk.prior_query_id == "older"


def test_an_empty_history_permits_anything():
    assert find_differencing_risk(people(40), [], threshold=11) is None


def test_ids_are_compared_as_strings():
    """A UUID object and its string form are the same patient."""
    history = [prior("q1", [1, 2, 3])]
    assert find_differencing_risk(["1", "2", "3"], history, threshold=11) is None


# ---------------------------------------------------------------------------
# History storage
# ---------------------------------------------------------------------------

def test_history_is_bounded_and_scoped_to_one_researcher(client):
    from api.models import CohortQueryLog, User

    session = client._session_factory()
    users = []
    for name in ("a", "b"):
        user = User(email=f"budget-{name}@example.com", password_hash="x",
                    name=name, user_type="researcher")
        session.add(user)
        session.flush()
        users.append(str(user.id))

    from datetime import datetime, timedelta
    base = datetime.utcnow()
    for index in range(DEFAULT_HISTORY_DEPTH + 10):
        session.add(CohortQueryLog(
            user_id=users[0], patient_set=[f"p{index}"], patient_count=1,
            created_at=base + timedelta(seconds=index),
        ))
    session.add(CohortQueryLog(user_id=users[1], patient_set=["other"], patient_count=1))
    session.commit()

    assert len(recent_history(session, CohortQueryLog, users[0])) == DEFAULT_HISTORY_DEPTH
    assert len(recent_history(session, CohortQueryLog, users[1])) == 1

    removed = prune_history(session, CohortQueryLog, users[0])
    session.commit()
    assert removed == 10
    assert session.query(CohortQueryLog).filter(
        CohortQueryLog.user_id == users[1]).count() == 1, "another researcher's history is untouched"
    session.close()


# ---------------------------------------------------------------------------
# End to end through the API
# ---------------------------------------------------------------------------

@pytest.fixture()
def cohort_client(client, make_user):
    """An approved researcher and 40 consented patients across two age bands."""
    from api.models import Consent, ExtractedMedicalData, PatientProfile

    headers, _ = make_user("budget@example.com", role="researcher",
                           verified=True, approved=True)
    with client._session_factory() as db:
        for index in range(40):
            patient = PatientProfile()
            db.add(patient)
            db.flush()
            db.add_all([
                Consent(patient_id=patient.id, consent_type="research_data_sharing", status="active"),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="c",
                    data_category="diagnosis", original_year=2020,
                    deidentified_data={"display": "AML"}),
                ExtractedMedicalData(
                    patient_id=patient.id, connection_id="c",
                    data_category="demographics", original_year=2020,
                    # One patient is 61; everyone else is 50.
                    deidentified_data={"age": 61 if index == 0 else 50}),
            ])
        db.commit()
    return client, headers


def build(client, headers, **criteria):
    response = client.post("/api/cohort/build", headers=headers, json=criteria)
    assert response.status_code == 200, response.text
    return response.json()


def test_the_narrowing_attack_is_blocked_end_to_end(cohort_client):
    """Ask for everyone, then everyone under 61, and subtract."""
    client, headers = cohort_client

    everyone = build(client, headers, cancer_types=["AML"])
    assert everyone["patient_count"] == 40
    assert everyone["suppressed"] is False

    all_but_one = build(client, headers, cancer_types=["AML"], age_max=60)
    assert all_but_one["suppressed"] is True
    assert all_but_one["patient_count"] == 0
    assert "differs from one of your earlier results" in all_but_one["suppression_reason"]


def test_a_blocked_query_does_not_itself_enter_the_history(cohort_client):
    """A refused answer disclosed nothing, so it must not constrain the next."""
    from api.models import CohortQueryLog

    client, headers = cohort_client
    build(client, headers, cancer_types=["AML"])
    build(client, headers, cancer_types=["AML"], age_max=60)

    with client._session_factory() as db:
        assert db.query(CohortQueryLog).count() == 1


def test_repeating_a_query_is_not_treated_as_an_attack(cohort_client):
    client, headers = cohort_client
    first = build(client, headers, cancer_types=["AML"])
    second = build(client, headers, cancer_types=["AML"])
    assert second["patient_count"] == first["patient_count"]
    assert second["suppressed"] is False


def test_another_researcher_is_not_constrained_by_someone_elses_history(cohort_client, make_user):
    """The disclosure is to a person. Two people each learned one thing."""
    client, headers = cohort_client
    build(client, headers, cancer_types=["AML"])

    other_headers, _ = make_user("budget-other@example.com", role="researcher",
                                 verified=True, approved=True)
    result = build(client, other_headers, cancer_types=["AML"], age_max=60)
    assert result["suppressed"] is False
    assert result["patient_count"] == 39


def test_a_small_cohort_is_still_suppressed_with_its_own_reason(cohort_client):
    client, headers = cohort_client
    result = build(client, headers, cancer_types=["AML"], age_min=61)
    assert result["suppressed"] is True
    assert "Fewer than" in result["suppression_reason"]
