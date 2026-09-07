"""Regression coverage for the closed-by-default pilot boundaries."""


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_self_service_registration_can_be_closed(client, monkeypatch):
    import api.main as main

    monkeypatch.setattr(main, "SELF_SERVICE_REGISTRATION_ENABLED", False)
    response = client.post(
        "/api/auth/register",
        json={
            "email": "closed@example.com",
            "password": "Str0ng!Passw0rd#2026",
            "name": "Closed Pilot",
            "user_type": "researcher",
        },
    )

    assert response.status_code == 403
    assert "registration is closed" in response.json()["detail"].lower()


def test_consent_text_is_readable_even_when_the_synthetic_workflow_is_closed(
        client, monkeypatch):
    """Replaces an earlier rule that hid the template entirely.

    Hiding it was meant to avoid implying a consent workflow existed where it
    did not. What it actually produced was a patient portal with nothing in
    it: production shipped with this flag unset, so anyone who signed up could
    read nothing, acknowledge nothing, and contribute nothing.

    The concern behind the old rule is real, and is now handled where it
    belongs — in what gets recorded, not in what can be read. See
    test_journeys.py: acknowledging while the pilot is closed records a
    prototype acknowledgement, which no query treats as authorisation.
    """
    import api.main as main

    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", False)
    response = client.get("/api/consent/templates")

    assert response.status_code == 200
    assert response.json(), "a patient with nothing to read is a dead end"
    # And it must still say plainly what it is. Normalised because the source
    # is wrapped, and a line break must not be able to hide a missing phrase.
    import re
    content = re.sub(r"\s+", " ", response.json()[0]["content"])
    assert "not a research consent form" in content
    assert "fictional or generated records only" in content


def test_fhir_upload_is_rejected_before_processing_when_closed(client, register, monkeypatch):
    import api.main as main

    patient = register("upload-gate@example.com", user_type="patient").json()
    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", False)
    response = client.post(
        "/api/patient/connections/fhir",
        headers=auth(patient["access_token"]),
        json={"source_name": "should-not-process.json", "bundle": {"resourceType": "Bundle"}},
    )

    assert response.status_code == 403
    assert "uploads are disabled" in response.json()["detail"].lower()


def test_activity_points_have_no_cash_value(client, register):
    patient = register("points-boundary@example.com", user_type="patient").json()
    response = client.get(
        "/api/patient/rewards",
        headers=auth(patient["access_token"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_monetary_value"] is False
    assert "cash_value" not in body


def test_marketplace_is_empty_when_release_workflow_is_closed(client):
    response = client.get("/api/marketplace/products")

    assert response.status_code == 200
    assert response.json() == []


def test_patient_study_enrollment_is_closed(client, register):
    patient = register("study-gate@example.com", user_type="patient").json()
    response = client.post(
        "/api/studies/00000000-0000-0000-0000-000000000000/join",
        headers=auth(patient["access_token"]),
    )

    assert response.status_code == 403
    assert "enrollment is not available" in response.json()["detail"].lower()


def test_researcher_cannot_open_recruitment_when_enrollment_is_closed(client, register):
    # Approved so the request reaches the enrollment flag under test rather
    # than stopping at the researcher-approval gate.
    from tests.conftest import approve_researcher
    researcher = register("recruitment-gate@example.com", user_type="researcher").json()
    approve_researcher(client, researcher["user"]["id"])
    response = client.put(
        "/api/researcher/studies/00000000-0000-0000-0000-000000000000/recruiting",
        headers=auth(researcher["access_token"]),
        json={"is_recruiting": True, "eligibility_summary": "Synthetic test only"},
    )

    assert response.status_code == 403
    assert "enrollment is not available" in response.json()["detail"].lower()
