"""No seeded hospital name may reach a caller.

Eight real hospitals were served by the public /api/institutions route as
though they were partner sites. Deleting those rows needs a database
credential; not serving them does not, and the harm was entirely in the
serving. These tests hold that line on every path that returns an
institution, so a new one cannot quietly reintroduce it.
"""
import pytest

from api.main import PLACEHOLDER_INSTITUTION_NAMES

SEEDED = sorted(PLACEHOLDER_INSTITUTION_NAMES)[:3]


@pytest.fixture()
def seeded_and_real(client):
    """A database in the state production is in: seeded rows plus a real one."""
    from api.models import Institution

    with client._session_factory() as db:
        for name in SEEDED:
            db.add(Institution(name=name, type="Cancer Center", is_active=True))
        db.add(Institution(name="Sample Academic Medical Center (demo)",
                           type="Academic Medical Center", is_active=True))
        db.commit()


def test_the_public_directory_serves_no_seeded_name(client, seeded_and_real):
    response = client.get("/api/institutions")
    assert response.status_code == 200
    names = {i["name"] for i in response.json()}
    assert not (names & set(SEEDED)), f"seeded names served: {names & set(SEEDED)}"


def test_the_public_directory_still_serves_real_entries(client, seeded_and_real):
    """Filtering must remove the seeded rows and nothing else."""
    names = {i["name"] for i in client.get("/api/institutions").json()}
    assert "Sample Academic Medical Center (demo)" in names


def test_cohort_feasibility_lists_no_seeded_name(client, seeded_and_real,
                                                 approved_researcher, monkeypatch):
    """The other path that returns institution names to a caller."""
    import api.main as main
    monkeypatch.setattr(main, "MIN_AGGREGATE_CELL_SIZE", 1)

    response = client.post("/api/cohort/build", headers=approved_researcher, json={})
    assert response.status_code == 200, response.text
    listed = set(response.json().get("available_institutions") or [])
    assert not (listed & set(SEEDED))


def test_an_inactive_real_institution_is_still_excluded(client):
    """The existing is_active rule must survive the new filter."""
    from api.models import Institution

    with client._session_factory() as db:
        db.add(Institution(name="Retired Site", is_active=False))
        db.commit()

    names = {i["name"] for i in client.get("/api/institutions").json()}
    assert "Retired Site" not in names


def test_every_seeded_name_is_filtered_not_just_the_ones_seen_in_production(client):
    """Production shows eight; the list holds eleven. All eleven must filter."""
    from api.models import Institution

    with client._session_factory() as db:
        for name in PLACEHOLDER_INSTITUTION_NAMES:
            db.add(Institution(name=name, is_active=True))
        db.commit()

    names = {i["name"] for i in client.get("/api/institutions").json()}
    assert names == set(), "no seeded name may be served"


def test_the_rows_are_filtered_not_deleted(client, seeded_and_real):
    """Filtering is a stopgap, and must not be mistaken for the migration.

    If serving started deleting rows as a side effect, the real cleanup would
    look done while never having been reviewed by an operator.
    """
    from api.models import Institution

    client.get("/api/institutions")
    with client._session_factory() as db:
        stored = {i.name for i in db.query(Institution).all()}
    assert set(SEEDED).issubset(stored), "the rows must still be there to delete"
