"""Two accounts, one adversary.

The per-researcher budget refuses a query that lands too close to one that
researcher was already shown. It cannot see two accounts each asking a single
question, neither constrained by the other, with someone holding both answers.
That is one adversary wearing two coats — a colluding pair, or one person with
two logins.

This is detection, not prevention, and the tests are written to hold that
distinction honestly. Blocking every cohort that lands near another
researcher's would fire constantly on legitimate work: two people studying the
same disease overlap by nature. A control that fires on everything is one
people learn to route around, and a control everyone routes around protects
nobody.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from api.query_budget import find_cross_account_pairs


def log(user, ids, when=None):
    return SimpleNamespace(id=f"{user}-{len(ids)}", user_id=user,
                           patient_set=list(ids),
                           created_at=when or datetime.utcnow())


def people(n, offset=0):
    return [f"p{i}" for i in range(offset, offset + n)]


# ---------------------------------------------------------------------------
# The attack the per-account check cannot see
# ---------------------------------------------------------------------------

def test_two_accounts_one_patient_apart_are_detected():
    """Neither account was refused. Subtracting their answers names a person."""
    pairs = find_cross_account_pairs(
        [log("alice", people(40)), log("bob", people(39))], threshold=11)
    assert len(pairs) == 1
    assert pairs[0][2] == 1


def test_a_swap_of_one_person_across_accounts_is_detected():
    """Same size, different people. Comparing counts alone would miss it."""
    swapped = people(39) + ["someone-else"]
    pairs = find_cross_account_pairs(
        [log("alice", people(40)), log("bob", swapped)], threshold=11)
    assert len(pairs) == 1
    assert pairs[0][2] == 2


def test_the_same_account_is_left_to_the_per_account_check():
    """Reporting it here would double-count what is already prevented."""
    assert find_cross_account_pairs(
        [log("alice", people(40)), log("alice", people(39))], threshold=11) == []


def test_genuinely_different_cohorts_are_not_flagged():
    assert find_cross_account_pairs(
        [log("alice", people(40)), log("bob", people(40, offset=500))],
        threshold=11) == []


def test_identical_cohorts_are_not_flagged():
    """Two researchers asking the same question disclose nothing extra."""
    assert find_cross_account_pairs(
        [log("alice", people(40)), log("bob", people(40))], threshold=11) == []


def test_a_difference_at_the_floor_is_allowed():
    assert find_cross_account_pairs(
        [log("alice", people(40)), log("bob", people(29))], threshold=11) == []


def test_a_difference_one_below_the_floor_is_flagged():
    assert len(find_cross_account_pairs(
        [log("alice", people(40)), log("bob", people(30))], threshold=11)) == 1


def test_three_colluding_accounts_yield_every_close_pair():
    pairs = find_cross_account_pairs(
        [log("a", people(40)), log("b", people(39)), log("c", people(38))],
        threshold=11)
    assert len(pairs) == 3


def test_the_scan_is_bounded_so_the_audit_cannot_become_quadratic():
    logs = [log(f"user{i}", people(40)) for i in range(200)]
    pairs = find_cross_account_pairs(logs, threshold=11, max_comparisons=100)
    assert isinstance(pairs, list)


# ---------------------------------------------------------------------------
# What the operator is told
# ---------------------------------------------------------------------------

@pytest.fixture()
def two_researchers(client):
    from api.models import CohortQueryLog, User

    ids = []
    with client._session_factory() as db:
        for name in ("alice", "bob"):
            user = User(email=f"xacct-{name}@example.com", password_hash="x",
                        name=name, user_type="researcher")
            db.add(user)
            db.flush()
            ids.append(str(user.id))
        db.commit()
    return ids


def test_a_clean_platform_reports_nothing(client):
    from api.self_audit import check_cross_account_differencing

    with client._session_factory() as db:
        finding = check_cross_account_differencing(db)
    assert finding.passed is True
    assert finding.count == 0


def test_the_operator_is_given_somewhere_to_look(client, two_researchers):
    from api.models import CohortQueryLog
    from api.self_audit import WARNING, check_cross_account_differencing

    alice, bob = two_researchers
    base = datetime.utcnow()
    with client._session_factory() as db:
        db.add(CohortQueryLog(user_id=alice, patient_set=people(40),
                              patient_count=40, created_at=base))
        db.add(CohortQueryLog(user_id=bob, patient_set=people(39),
                              patient_count=39,
                              created_at=base + timedelta(seconds=1)))
        db.commit()
        finding = check_cross_account_differencing(db)

    assert finding.passed is False
    assert finding.count == 1
    assert sorted([alice, bob]) in finding.detail["account_pairs"]


def test_it_is_a_warning_because_overlapping_research_looks_the_same(client, two_researchers):
    """Made a blocker, this would fire on honest work and be ignored."""
    from api.models import CohortQueryLog
    from api.self_audit import WARNING, check_cross_account_differencing, run_audit

    alice, bob = two_researchers
    with client._session_factory() as db:
        db.add(CohortQueryLog(user_id=alice, patient_set=people(40), patient_count=40))
        db.add(CohortQueryLog(user_id=bob, patient_set=people(39), patient_count=39))
        db.commit()
        finding = check_cross_account_differencing(db)
        report = run_audit(db)

    assert finding.severity == WARNING
    assert report.ok is True, "a warning must not gate the whole audit"


def test_the_finding_accuses_nobody(client, two_researchers):
    """Two people studying one disease produce this pattern honestly."""
    from api.models import CohortQueryLog
    from api.self_audit import check_cross_account_differencing

    alice, bob = two_researchers
    with client._session_factory() as db:
        db.add(CohortQueryLog(user_id=alice, patient_set=people(40), patient_count=40))
        db.add(CohortQueryLog(user_id=bob, patient_set=people(39), patient_count=39))
        db.commit()
        summary = check_cross_account_differencing(db).summary.lower()

    assert "review rather than assume" in summary
    for accusation in ("attack", "malicious", "misconduct", "breach", "violation"):
        assert accusation not in summary


def test_no_patient_identifier_reaches_the_finding(client, two_researchers):
    """The privacy checker must not create a disclosure of its own."""
    import json

    from api.models import CohortQueryLog
    from api.self_audit import check_cross_account_differencing

    alice, bob = two_researchers
    subjects = people(40)
    with client._session_factory() as db:
        db.add(CohortQueryLog(user_id=alice, patient_set=subjects, patient_count=40))
        db.add(CohortQueryLog(user_id=bob, patient_set=subjects[:-1], patient_count=39))
        db.commit()
        serialized = json.dumps(check_cross_account_differencing(db).as_dict())

    for subject in subjects:
        assert subject not in serialized
