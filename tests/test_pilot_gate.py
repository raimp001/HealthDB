"""The closed-pilot registration gate."""
import pytest


@pytest.fixture()
def gate_closed(client, monkeypatch):
    import api.main as main
    monkeypatch.setattr(main, "ALLOW_SELF_SERVICE_REGISTRATION", False)
    return client


class TestRegistrationGate:
    def test_signup_refused_when_pilot_closed(self, gate_closed):
        r = gate_closed.post("/api/auth/register", json={
            "email": "walkup@example.com",
            "password": "Str0ng!Passw0rd#2026",
            "name": "Walk Up",
            "user_type": "researcher",
        })
        assert r.status_code == 403
        assert "closed pilot" in r.json()["detail"].lower()

    def test_signup_allowed_when_open(self, client):
        r = client.post("/api/auth/register", json={
            "email": "invited@example.com",
            "password": "Str0ng!Passw0rd#2026",
            "name": "Invited",
            "user_type": "researcher",
        })
        assert r.status_code == 200

    def test_gate_does_not_weaken_role_validation(self, client):
        """The gate must not become the only thing stopping escalation."""
        r = client.post("/api/auth/register", json={
            "email": "still-blocked@example.com",
            "password": "Str0ng!Passw0rd#2026",
            "name": "Nope",
            "user_type": "admin",
        })
        assert r.status_code == 422
