"""Complete route/method authorization matrix.

Enumerates every registered route from the live FastAPI app rather than a
hand-maintained list, so a new endpoint added without a gate fails here
instead of shipping. Covers GET, POST, PUT, PATCH and DELETE.

No test in this file may skip: a skipped authorization check is
indistinguishable from an absent one.
"""
import re

import pytest

import api.main as main

# Routes intentionally reachable without authentication.
PUBLIC_ALLOWLIST = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/request-password-reset",
    "/api/auth/reset-password",
    "/api/auth/verify-email",
    "/api/institutions",
    "/api/stats/platform",
    "/api/stats/cancer-types",
    "/api/contact",
    "/api/marketplace/inquiry",
    "/api/marketplace/products",
    "/api/diseases/variable-sets",
    # Reference and catalogue data with no subject: consent template text,
    # marketplace listings, and the disease variable dictionary. Each was
    # reviewed and is intentionally readable without an account.
    "/api/consent/templates",
    "/api/marketplace/products/{product_id}",
    "/api/diseases/{disease_name}/variables",
    "/api/docs",
    "/api/redoc",
}

RESEARCH_PREFIXES = ("/api/researcher", "/api/cohort", "/api/extraction",
                     "/api/regulatory", "/api/studies", "/api/study",
                     "/api/analytics")
INSTITUTION_PREFIXES = ("/api/institution/", "/api/emr/")
PATIENT_PREFIXES = ("/api/patient/",)

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def app_routes():
    """(method, path, dependency-source) for every /api route."""
    import inspect as pyinspect
    out = []
    for route in main.app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api"):
            continue
        try:
            source = pyinspect.getsource(route.endpoint)
        except (OSError, TypeError):
            source = ""
        for method in getattr(route, "methods", set()) & METHODS:
            out.append((method, path, source))
    return out


def concrete(path: str) -> str:
    """Fill path params so the route matches; the id need not exist."""
    return re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)


def call(client, method, path, headers=None):
    return client.request(method, concrete(path), headers=headers or {}, json={})


class TestEveryRouteIsGated:
    def test_no_route_uses_a_jwt_claim_for_authorization(self):
        """The token's role claim must never decide what a request may do."""
        offenders = []
        for method, path, source in app_routes():
            # Reading token_data["sub"] for identity is fine; branching on the
            # "type" claim is not.
            if re.search(r'token_data(?:\.get\(|\[)["\']type["\']', source):
                offenders.append(f"{method} {path}")
        assert not offenders, (
            "these handlers branch on the JWT role claim instead of the "
            f"database: {offenders}"
        )

    @pytest.mark.parametrize("method,path", [
        (m, p) for m, p, _ in app_routes() if p not in PUBLIC_ALLOWLIST
    ])
    def test_protected_routes_reject_anonymous_callers(self, client, method, path):
        r = call(client, method, path)
        assert r.status_code in (401, 403, 405, 422), (
            f"{method} {path} served an anonymous caller (status {r.status_code})"
        )


class TestResearchSurface:
    """Research routes need an active, verified, approved researcher."""

    RESEARCH_ROUTES = [(m, p) for m, p, _ in app_routes()
                       if p.startswith(RESEARCH_PREFIXES) and p not in PUBLIC_ALLOWLIST]

    @pytest.mark.parametrize("method,path", RESEARCH_ROUTES)
    def test_patient_token_is_refused(self, client, patient_user, method, path):
        r = call(client, method, path, patient_user)
        assert r.status_code != 200, f"a patient reached {method} {path}"
        assert r.status_code in (401, 403, 404, 405, 422), (
            f"{method} {path} returned {r.status_code} for a patient"
        )

    @pytest.mark.parametrize("method,path", RESEARCH_ROUTES)
    def test_unapproved_researcher_is_refused(self, client, unapproved_researcher,
                                              method, path):
        r = call(client, method, path, unapproved_researcher)
        assert r.status_code != 200, (
            f"an unapproved researcher reached {method} {path}"
        )

    def test_approval_message_explains_the_state(self, client, unapproved_researcher):
        r = client.get("/api/researcher/studies", headers=unapproved_researcher)
        assert r.status_code == 403
        assert "pending approval" in r.json()["detail"].lower()

    def test_unverified_researcher_is_refused_even_when_approved(self, client, make_user):
        headers, _ = make_user("unverified@example.com", role="researcher",
                               verified=False, approved=True)
        r = client.get("/api/researcher/studies", headers=headers)
        assert r.status_code == 403
        assert "verify" in r.json()["detail"].lower()

    def test_approved_researcher_is_allowed(self, client, approved_researcher):
        r = client.get("/api/researcher/studies", headers=approved_researcher)
        assert r.status_code == 200, r.text


class TestInstitutionSurface:
    INSTITUTION_ROUTES = [(m, p) for m, p, _ in app_routes()
                          if p.startswith(INSTITUTION_PREFIXES)]

    @pytest.mark.parametrize("method,path", INSTITUTION_ROUTES)
    def test_patient_token_is_refused(self, client, patient_user, method, path):
        r = call(client, method, path, patient_user)
        assert r.status_code != 200, f"a patient reached {method} {path}"

    @pytest.mark.parametrize("method,path", INSTITUTION_ROUTES)
    def test_approved_researcher_is_refused(self, client, approved_researcher,
                                            method, path):
        r = call(client, method, path, approved_researcher)
        assert r.status_code != 200, f"a researcher reached {method} {path}"

    def test_institution_account_without_an_institution_is_refused(self, client, make_user):
        """An unscoped institution account could otherwise read every institution."""
        headers, _ = make_user("unscoped@example.com", role="institution",
                               verified=True, institution_id=None)
        r = client.get("/api/institution/agreements", headers=headers)
        assert r.status_code == 403
        assert "not linked" in r.json()["detail"].lower()

    def test_scoped_institution_account_is_allowed(self, client, institution_user):
        headers, _ = institution_user
        r = client.get("/api/institution/agreements", headers=headers)
        assert r.status_code == 200, r.text


class TestPatientSurface:
    PATIENT_ROUTES = [(m, p) for m, p, _ in app_routes()
                      if p.startswith(PATIENT_PREFIXES)]

    @pytest.mark.parametrize("method,path", PATIENT_ROUTES)
    def test_researcher_token_is_refused(self, client, approved_researcher,
                                         method, path):
        r = call(client, method, path, approved_researcher)
        assert r.status_code != 200, f"a researcher reached {method} {path}"


class TestAccountDeactivation:
    """A token must stop working the moment the account is deactivated."""

    def test_deactivated_user_is_refused_everywhere(self, client, make_user):
        headers, user_id = make_user("deactivate@example.com", role="researcher",
                                     verified=True, approved=True)
        assert client.get("/api/researcher/studies", headers=headers).status_code == 200

        from api.models import User
        session = client._session_factory()
        session.query(User).filter(User.id == user_id).update({"is_active": False})
        session.commit()
        session.close()

        for path in ["/api/researcher/studies", "/api/cohort/saved", "/api/auth/me"]:
            r = client.get(path, headers=headers)
            assert r.status_code == 401, (
                f"{path} still served a deactivated account (status {r.status_code})"
            )

    def test_revoked_researcher_approval_takes_effect_immediately(self, client, make_user):
        headers, user_id = make_user("revoke-me@example.com", role="researcher",
                                     verified=True, approved=True)
        assert client.get("/api/researcher/studies", headers=headers).status_code == 200

        from api.models import User
        session = client._session_factory()
        session.query(User).filter(User.id == user_id).update(
            {"researcher_approved_at": None})
        session.commit()
        session.close()

        r = client.get("/api/researcher/studies", headers=headers)
        assert r.status_code == 403, "revoked approval did not take effect"
