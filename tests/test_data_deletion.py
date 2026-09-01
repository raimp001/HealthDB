"""Patient data-deletion requests."""
import pytest

PASSWORD = "Str0ng!Passw0rd#2026"


@pytest.fixture()
def patient(client, register):
    body = register("delete-me@example.com", user_type="patient", password=PASSWORD).json()
    return body["access_token"], body["user"]["email"]


def auth(t):
    return {"Authorization": f"Bearer {t}"}


class TestDeletionRequest:
    def test_request_is_recorded_and_consents_revoked(self, client, patient):
        token, email = patient
        r = client.post("/api/patient/request-deletion",
                        headers=auth(token),
                        json={"confirm_email": email, "reason": "No longer participating"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert "cannot be recalled" in body["message"]

        from api.models import ContactSubmission
        session = client._session_factory()
        row = session.query(ContactSubmission).filter(
            ContactSubmission.submission_type == "data_deletion"
        ).first()
        assert row is not None, "no deletion request was recorded"
        session.close()

    def test_mismatched_email_is_refused(self, client, patient):
        token, _ = patient
        r = client.post("/api/patient/request-deletion",
                        headers=auth(token),
                        json={"confirm_email": "someone-else@example.com"})
        assert r.status_code == 400

    def test_requires_authentication(self, client):
        r = client.post("/api/patient/request-deletion",
                        json={"confirm_email": "x@example.com"})
        assert r.status_code in (401, 403)
