"""Getting the first admin onto a hosted deployment, and the migration it unlocks.

Without an admin nobody can approve a researcher, so the research half of the
platform is dead on arrival. Roles are granted by a CLI that needs a database
URL, and registration refuses to mint privileged accounts — correctly. That
left no path at all on a hosted deployment.

These cover the narrow path added for it, and the ways it must refuse to
widen.
"""
from datetime import datetime

import pytest

import api.main as main


@pytest.fixture()
def registered(client, register):
    body = register("boot-admin@example.com").json()
    return body["user"]["id"], body["access_token"]


def user_type(client, user_id):
    from api.models import User

    with client._session_factory() as db:
        return db.query(User).filter(User.id == user_id).one().user_type


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def test_nothing_happens_without_the_variable(client, registered, monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_EMAIL", raising=False)
    assert main.promote_bootstrap_admin(client._session_factory) is False


def test_a_registered_account_is_promoted(client, registered, monkeypatch):
    user_id, _ = registered
    assert user_type(client, user_id) == "researcher"

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    assert main.promote_bootstrap_admin(client._session_factory) is True
    assert user_type(client, user_id) == "admin"


def test_promotion_is_idempotent(client, registered, monkeypatch):
    """Every cold start runs this. The second one must be a no-op."""
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    assert main.promote_bootstrap_admin(client._session_factory) is True
    assert main.promote_bootstrap_admin(client._session_factory) is False


def test_the_address_is_matched_regardless_of_case(client, registered, monkeypatch):
    user_id, _ = registered
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "  Boot-Admin@Example.COM  ")
    assert main.promote_bootstrap_admin(client._session_factory) is True
    assert user_type(client, user_id) == "admin"


def test_an_unregistered_address_promotes_nobody(client, monkeypatch):
    """It grants a role. It must never mint an identity."""
    from api.models import User

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "nobody-here@example.com")
    assert main.promote_bootstrap_admin(client._session_factory) is False
    with client._session_factory() as db:
        assert db.query(User).filter(User.user_type == "admin").count() == 0


def test_unsetting_the_variable_does_not_demote(client, registered, monkeypatch):
    """Removing admin should be a decision, not a config side effect."""
    user_id, _ = registered
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)

    monkeypatch.delenv("BOOTSTRAP_ADMIN_EMAIL", raising=False)
    main.promote_bootstrap_admin(client._session_factory)
    assert user_type(client, user_id) == "admin"


def test_a_failure_to_promote_is_never_fatal(client, monkeypatch):
    """This runs at import. An exception here takes down every request."""
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")

    def explode():
        raise RuntimeError("database unreachable")

    assert main.promote_bootstrap_admin(explode) is False


def test_registration_still_refuses_to_mint_an_admin(client):
    """The bootstrap must not have opened a second door."""
    response = client.post("/api/auth/register", json={
        "email": "self-made-admin@example.com", "password": "Str0ng!Passw0rd#2026",
        "name": "Nope", "user_type": "admin"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# What the promotion unlocks
# ---------------------------------------------------------------------------

def test_the_promoted_account_can_reach_the_operator_inbox(client, registered, monkeypatch):
    """The point of all this: the admin surface stops being decorative."""
    _, token = registered
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/admin/overview", headers=headers).status_code == 403

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)
    assert client.get("/api/admin/overview", headers=headers).status_code == 200


def test_the_audit_reports_when_no_admin_exists(client):
    from api.self_audit import check_admin_bootstrap

    with client._session_factory() as db:
        finding = check_admin_bootstrap(db)
    assert finding.passed is False
    assert "No admin account exists" in finding.summary


def test_the_audit_reports_a_bootstrap_left_armed(client, registered, monkeypatch):
    """While it is set, editing deployment config grants the admin role."""
    from api.self_audit import check_admin_bootstrap

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)

    with client._session_factory() as db:
        finding = check_admin_bootstrap(db)
    assert finding.passed is False
    assert "still set" in finding.summary
    assert finding.detail["bootstrap_armed"] is True


def test_the_audit_passes_once_an_admin_exists_and_the_variable_is_gone(
        client, registered, monkeypatch):
    from api.self_audit import check_admin_bootstrap

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_EMAIL", raising=False)

    with client._session_factory() as db:
        finding = check_admin_bootstrap(db)
    assert finding.passed is True
    assert finding.detail["admin_count"] == 1


def test_no_email_address_appears_in_the_audit_finding(client, registered, monkeypatch):
    """A findings payload is the wrong place to carry a real person's address."""
    import json

    from api.self_audit import check_admin_bootstrap

    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)
    with client._session_factory() as db:
        serialized = json.dumps(check_admin_bootstrap(db).as_dict())
    assert "boot-admin@example.com" not in serialized


# ---------------------------------------------------------------------------
# The migration, now reachable by a person rather than a database URL
# ---------------------------------------------------------------------------

@pytest.fixture()
def admin_headers(client, registered, monkeypatch):
    _, token = registered
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "boot-admin@example.com")
    main.promote_bootstrap_admin(client._session_factory)
    return {"Authorization": f"Bearer {token}"}


def test_a_researcher_cannot_reach_the_migration(client, approved_researcher):
    assert client.get("/api/admin/maintenance/date-truncation",
                      headers=approved_researcher).status_code == 403
    assert client.post("/api/admin/maintenance/date-truncation",
                       headers=approved_researcher,
                       json={"confirm": "truncate-dates-permanently"}).status_code == 403


def test_an_anonymous_caller_cannot_reach_the_migration(client):
    assert client.get("/api/admin/maintenance/date-truncation").status_code in (401, 403)


def test_the_preview_reports_state_and_changes_nothing(client, admin_headers):
    response = client.get("/api/admin/maintenance/date-truncation", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reversible"] is False
    assert "rows_with_month_and_day" in body


def test_running_without_the_exact_confirmation_is_refused(client, admin_headers):
    """A replayed or stray POST must not destroy anything."""
    for bad in ["yes", "", "truncate", "TRUNCATE-DATES-PERMANENTLY"]:
        response = client.post("/api/admin/maintenance/date-truncation",
                               headers=admin_headers, json={"confirm": bad})
        assert response.status_code == 422, f"{bad!r} was accepted"


def test_running_on_an_already_migrated_database_is_harmless(client, admin_headers):
    """The test schema has no original_date column; this is the applied state."""
    response = client.post("/api/admin/maintenance/date-truncation",
                           headers=admin_headers,
                           json={"confirm": "truncate-dates-permanently"})
    assert response.status_code == 200, response.text
    assert response.json()["applied"] is False
    assert "Already applied" in response.json()["reason"]
