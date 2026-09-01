"""Regression tests for the registration privilege-escalation vulnerability.

The bug: POST /api/auth/register sanitised user_type before writing the user
row, but minted the JWT from the raw request body. Sending
{"user_type": "admin"} returned a token with type=admin, and require_role()
trusted that claim, granting access to the regulatory approval endpoint.
"""
import pytest
from jose import jwt

SECRET = "test-only-secret-not-used-anywhere-else"
APPROVE_URL = "/api/regulatory/00000000-0000-0000-0000-000000000000/approve"


class TestRegistrationRoleValidation:
    @pytest.mark.parametrize("bad_role", ["admin", "institution", "superuser", "ADMIN", "root"])
    def test_privileged_roles_are_rejected(self, register, bad_role):
        """The original exploit payload must not create an account at all."""
        r = register(f"escalate-{bad_role}@example.com", user_type=bad_role)
        assert r.status_code == 422, (
            f"user_type={bad_role!r} was accepted; expected schema rejection"
        )

    @pytest.mark.parametrize("good_role", ["patient", "researcher"])
    def test_self_service_roles_are_allowed(self, register, good_role):
        r = register(f"ok-{good_role}@example.com", user_type=good_role)
        assert r.status_code == 200, r.text
        assert r.json()["user"]["user_type"] == good_role

    def test_token_role_matches_persisted_role(self, register):
        """The JWT must never carry a role the database does not agree with."""
        r = register("claims@example.com", user_type="researcher")
        assert r.status_code == 200
        body = r.json()
        claims = jwt.decode(body["access_token"], SECRET, algorithms=["HS256"])
        assert claims["type"] == body["user"]["user_type"] == "researcher"

    def test_default_role_is_researcher(self, client):
        r = client.post("/api/auth/register", json={
            "email": "default@example.com",
            "password": "Str0ng!Passw0rd#2026",
            "name": "Default",
        })
        assert r.status_code == 200
        assert r.json()["user"]["user_type"] == "researcher"


class TestForgedTokenCannotEscalate:
    def test_forged_admin_claim_is_refused(self, client, register):
        """A validly-signed token whose role claim was tampered with must fail.

        This is the defence-in-depth half of the fix: even if an attacker can
        mint a token with type=admin, require_role resolves the role from the
        database, where only patient/researcher can exist.
        """
        r = register("forger@example.com", user_type="researcher")
        user_id = r.json()["user"]["id"]

        forged = jwt.encode(
            {"sub": user_id, "type": "admin", "exp": 9999999999, "iat": 1600000000},
            SECRET, algorithm="HS256",
        )
        resp = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {forged}"})
        assert resp.status_code == 403, (
            f"forged admin token was honoured (status {resp.status_code}); "
            "role must come from the database, not the JWT claim"
        )

    def test_researcher_token_cannot_approve(self, client, register):
        r = register("plain@example.com", user_type="researcher")
        token = r.json()["access_token"]
        resp = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_patient_token_cannot_approve(self, client, register):
        r = register("pt@example.com", user_type="patient")
        token = r.json()["access_token"]
        resp = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_unauthenticated_cannot_approve(self, client):
        assert client.post(APPROVE_URL).status_code in (401, 403)

    @pytest.mark.parametrize("bad", ["not-a-token", "a.b.c"])
    def test_garbage_tokens_rejected(self, client, bad):
        r = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {bad}"})
        assert r.status_code == 401

    def test_token_signed_with_wrong_secret_rejected(self, client, register):
        r = register("wrongsig@example.com")
        user_id = r.json()["user"]["id"]
        forged = jwt.encode(
            {"sub": user_id, "type": "admin", "exp": 9999999999},
            "attacker-controlled-secret", algorithm="HS256",
        )
        resp = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {forged}"})
        assert resp.status_code == 401

    def test_deactivated_user_token_stops_working(self, client, register):
        """A token outlives its account only until the next privileged call."""
        from api.models import User
        r = register("deact@example.com", user_type="researcher")
        token = r.json()["access_token"]
        user_id = r.json()["user"]["id"]

        session = client._session_factory()
        session.query(User).filter(User.id == user_id).update({"is_active": False})
        session.commit()
        session.close()

        resp = client.post(APPROVE_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
