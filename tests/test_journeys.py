"""Both journeys, end to end, through the API only.

Every dead end these cover was live in production. An account could be
created and then nothing could be done with it, in three separate ways:

* No admin could exist, so no researcher could be approved, so the research
  half of the product was unreachable.
* Approval demanded email verification on a platform with no email, so even
  an admin could not have approved anyone.
* A patient had no consent text to read, and could not have signed it if
  they had.

Each of those looked fine in the code and in the unit tests. They only show
up if you walk the whole path, which is what this does. Nothing is inserted
directly except clinical records, because those are the one thing that
genuinely arrives from outside — if a step needs a database write to pass, it
is not a working product.
"""
import pytest

import api.main as main
from tests.conftest import VALID_PASSWORD


def register(client, email, role="researcher"):
    response = client.post("/api/auth/register", json={
        "email": email, "password": VALID_PASSWORD,
        "name": email.split("@")[0], "user_type": role})
    assert response.status_code == 200, response.text
    return response.json()


def login(client, email):
    response = client.post("/api/auth/login",
                           json={"email": email, "password": VALID_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def operator(client, monkeypatch):
    """An admin, obtained the only way a hosted deployment can obtain one."""
    register(client, "journey-operator@example.com")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "journey-operator@example.com")
    assert main.promote_bootstrap_admin(client._session_factory) is True
    # The role is read from the persisted row, so the session is re-established.
    return login(client, "journey-operator@example.com")


# ---------------------------------------------------------------------------
# Researcher
# ---------------------------------------------------------------------------

def test_a_researcher_can_get_from_signup_to_a_study(client, operator):
    """The whole path, with no database write anywhere in it."""
    body = register(client, "journey-researcher@example.com")
    researcher_id = body["user"]["id"]
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    blocked = client.post("/api/researcher/studies", headers=headers, json={"name": "Too soon"})
    assert blocked.status_code == 403

    inbox = client.get("/api/admin/overview", headers=operator)
    assert inbox.status_code == 200, inbox.text
    assert any(u["id"] == researcher_id for u in inbox.json()["researchers"]), \
        "an applicant who cannot be seen cannot be approved"

    approved = client.post(f"/api/admin/researchers/{researcher_id}/decision",
                           headers=operator, json={"decision": "confirm-identity"})
    assert approved.status_code == 200, approved.text
    assert client.post(f"/api/admin/researchers/{researcher_id}/decision",
                       headers=operator, json={"decision": "approve"}).status_code == 200

    headers = login(client, "journey-researcher@example.com")
    study = client.post("/api/researcher/studies", headers=headers, json={"name": "Journey study"})
    assert study.status_code == 200, study.text


def test_approval_will_not_proceed_until_identity_is_confirmed(client, operator):
    """Two decisions. Doing both in one click would hide the second."""
    researcher_id = register(client, "journey-unconfirmed@example.com")["user"]["id"]

    refused = client.post(f"/api/admin/researchers/{researcher_id}/decision",
                          headers=operator, json={"decision": "approve"})
    assert refused.status_code == 409
    assert "identity" in refused.json()["detail"].lower()


def test_identity_confirmation_cannot_be_withdrawn_under_a_live_approval(client, operator):
    """Otherwise an approved researcher would sit on an unconfirmed identity."""
    researcher_id = register(client, "journey-withdraw@example.com")["user"]["id"]
    for decision in ("confirm-identity", "approve"):
        assert client.post(f"/api/admin/researchers/{researcher_id}/decision",
                           headers=operator, json={"decision": decision}).status_code == 200

    refused = client.post(f"/api/admin/researchers/{researcher_id}/decision",
                          headers=operator, json={"decision": "withdraw-identity"})
    assert refused.status_code == 409


def test_the_gate_does_not_ask_for_an_email_link_that_cannot_be_sent(client):
    """There is no email system. The message must not tell someone to wait."""
    body = register(client, "journey-message@example.com")
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    detail = client.post("/api/researcher/studies", headers=headers,
                         json={"name": "x"}).json()["detail"].lower()
    assert "verify your email" not in detail
    assert "identity" in detail


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

def test_a_patient_can_read_acknowledge_and_revoke(client):
    """Production shipped with nothing here for a patient to do at all."""
    body = register(client, "journey-patient@example.com", role="patient")
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    templates = client.get("/api/consent/templates", headers=headers)
    assert templates.status_code == 200
    assert templates.json(), "a patient with nothing to acknowledge is a dead end"

    signed = client.post("/api/consent/sign", headers=headers, json={
        "template_id": templates.json()[0]["id"], "signature": "Patient",
        "consent_options": {"research_data_sharing": True}})
    assert signed.status_code == 200, signed.text

    active = [c for c in client.get("/api/patient/consents", headers=headers).json()
              if c["status"] == "active"]
    assert active, "a signed acknowledgement must be visible to the person who signed it"

    revoked = client.post(f"/api/consent/{active[0]['id']}/revoke", headers=headers)
    assert revoked.status_code == 200, revoked.text


def test_listing_the_template_does_not_write_to_the_database(client):
    """It used to be created on demand, so an unauthenticated GET wrote rows."""
    from api.models import ConsentTemplate

    with client._session_factory() as db:
        before = db.query(ConsentTemplate).count()
    for _ in range(3):
        assert client.get("/api/consent/templates").status_code == 200
    with client._session_factory() as db:
        assert db.query(ConsentTemplate).count() == before


def test_seeding_the_template_is_idempotent(client):
    from api.models import ConsentTemplate

    main.ensure_consent_template(client._session_factory)
    main.ensure_consent_template(client._session_factory)
    with client._session_factory() as db:
        assert db.query(ConsentTemplate).filter(
            ConsentTemplate.name == main.PILOT_CONSENT_TEMPLATE_NAME).count() == 1


def test_every_patient_route_answers_for_a_brand_new_account(client):
    """A fresh account must not meet an error on any screen it can open."""
    body = register(client, "journey-fresh@example.com", role="patient")
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    for path in ("/api/patient/profile", "/api/patient/consents",
                 "/api/patient/data-access-log", "/api/patient/contribution",
                 "/api/patient/data-releases", "/api/patient/study-results",
                 "/api/patient/connections", "/api/patient/extracted-data",
                 "/api/patient/data-summary"):
        assert client.get(path, headers=headers).status_code == 200, path


# ---------------------------------------------------------------------------
# The acknowledgement must never quietly become a research consent
# ---------------------------------------------------------------------------

def test_an_acknowledgement_is_not_recorded_as_research_consent_when_uploads_are_off(
        client, monkeypatch):
    """The distinction that stops a prototype tick-box being upgraded later.

    Someone who acknowledged a simulation has not agreed to their records
    being drawn into a cohort. If both recorded the same consent type,
    enabling uploads later would silently convert one into the other with
    nobody deciding to.
    """
    from api.models import Consent

    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", False)
    body = register(client, "journey-proto@example.com", role="patient")
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    template_id = client.get("/api/consent/templates", headers=headers).json()[0]["id"]
    assert client.post("/api/consent/sign", headers=headers, json={
        "template_id": template_id, "signature": "P",
        "consent_options": {"research_data_sharing": True}}).status_code == 200

    with client._session_factory() as db:
        types = {c.consent_type for c in db.query(Consent).all()}
    assert types == {"prototype_acknowledgement"}
    assert "research_data_sharing" not in types


def test_a_prototype_acknowledgement_never_makes_records_cohort_eligible(client, monkeypatch):
    """The type exists precisely so no query treats it as authorisation."""
    from api.models import Consent, ExtractedMedicalData, PatientProfile

    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", False)
    body = register(client, "journey-proto2@example.com", role="patient")
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    template_id = client.get("/api/consent/templates", headers=headers).json()[0]["id"]
    client.post("/api/consent/sign", headers=headers, json={
        "template_id": template_id, "signature": "P",
        "consent_options": {"research_data_sharing": True}})

    with client._session_factory() as db:
        profile_id = str(db.query(PatientProfile).filter(
            PatientProfile.user_id == body["user"]["id"]).one().id)
        db.add(ExtractedMedicalData(
            patient_id=profile_id, connection_id="synthetic",
            data_category="diagnosis", original_year=2020,
            deidentified_data={"display": "AML"}))
        db.commit()
        eligible = {str(p) for p in main._consented_patient_ids(db)}

    assert profile_id not in eligible


def test_the_real_consent_is_recorded_where_the_pilot_is_open(client, monkeypatch):
    from api.models import Consent

    monkeypatch.setattr(main, "SYNTHETIC_FHIR_UPLOADS_ENABLED", True)
    body = register(client, "journey-real@example.com", role="patient")
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    template_id = client.get("/api/consent/templates", headers=headers).json()[0]["id"]
    assert client.post("/api/consent/sign", headers=headers, json={
        "template_id": template_id, "signature": "P",
        "consent_options": {"research_data_sharing": True}}).status_code == 200

    with client._session_factory() as db:
        assert {c.consent_type for c in db.query(Consent).all()} == {"research_data_sharing"}
