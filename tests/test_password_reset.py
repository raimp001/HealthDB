"""Password reset and email verification.

Neither workflow existed: "Forgot?" linked to a contact page, and is_verified
was a column nothing ever set.
"""
import pytest

import api.main as main

PASSWORD = "Str0ng!Passw0rd#2026"
NEW_PASSWORD = "Even5tronger!Pass#2026"


def issued_token(client, email, purpose):
    """Read the raw token out of the delivery call, as an inbox would."""
    sent = {}
    original = main.deliver_notification

    def capture(subject, body):
        sent["body"] = body
        return original(subject, body)

    main.deliver_notification = capture
    try:
        client.post("/api/auth/request-password-reset", json={"email": email})
    finally:
        main.deliver_notification = original
    body = sent.get("body", "")
    return body.split("token=")[-1].strip() if "token=" in body else None


@pytest.fixture()
def account(client, register):
    register("reset-me@example.com", user_type="researcher", password=PASSWORD)
    return "reset-me@example.com"


class TestPasswordReset:
    def test_reset_completes_and_new_password_works(self, client, account):
        token = issued_token(client, account, "password_reset")
        assert token, "no reset token was delivered"

        r = client.post("/api/auth/reset-password",
                        json={"token": token, "new_password": NEW_PASSWORD})
        assert r.status_code == 200, r.text

        assert client.post("/api/auth/login",
                           json={"email": account, "password": NEW_PASSWORD}).status_code == 200
        assert client.post("/api/auth/login",
                           json={"email": account, "password": PASSWORD}).status_code == 401

    def test_token_is_single_use(self, client, account):
        token = issued_token(client, account, "password_reset")
        first = client.post("/api/auth/reset-password",
                            json={"token": token, "new_password": NEW_PASSWORD})
        assert first.status_code == 200
        replay = client.post("/api/auth/reset-password",
                             json={"token": token, "new_password": "Third!Passw0rd#2026"})
        assert replay.status_code == 400

    def test_invalid_token_rejected(self, client, account):
        r = client.post("/api/auth/reset-password",
                        json={"token": "not-a-real-token", "new_password": NEW_PASSWORD})
        assert r.status_code == 400

    def test_weak_new_password_rejected(self, client, account):
        token = issued_token(client, account, "password_reset")
        r = client.post("/api/auth/reset-password",
                        json={"token": token, "new_password": "short"})
        assert r.status_code == 400

    def test_unknown_address_does_not_leak_existence(self, client, account):
        known = client.post("/api/auth/request-password-reset", json={"email": account})
        unknown = client.post("/api/auth/request-password-reset",
                              json={"email": "nobody@example.com"})
        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json(), "response differs by account existence"


class TestEmailVerification:
    def test_verification_flow_sets_is_verified(self, client, register):
        body = register("verify-me@example.com", user_type="researcher").json()
        token_hdr = {"Authorization": f"Bearer {body['access_token']}"}
        assert body["user"]["is_verified"] is False

        sent = {}
        original = main.deliver_notification
        main.deliver_notification = lambda s, b: sent.setdefault("body", b)
        try:
            r = client.post("/api/auth/request-verification", headers=token_hdr)
        finally:
            main.deliver_notification = original
        assert r.status_code == 200

        raw = sent["body"].split("token=")[-1].strip()
        confirm = client.post("/api/auth/verify-email", json={"token": raw})
        assert confirm.status_code == 200

        from api.models import User
        session = client._session_factory()
        user = session.query(User).filter(User.email == "verify-me@example.com").first()
        assert user.is_verified is True
        session.close()

    def test_verification_requires_authentication(self, client):
        assert client.post("/api/auth/request-verification").status_code in (401, 403)

    def test_bad_verification_token_rejected(self, client):
        r = client.post("/api/auth/verify-email", json={"token": "bogus"})
        assert r.status_code == 400
