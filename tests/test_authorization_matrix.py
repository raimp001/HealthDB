"""Complete route/role authorization matrix.

Enumerates every registered route from the live FastAPI app rather than a
hand-maintained list, so an endpoint added without a gate fails here instead
of shipping.

Nothing in this file skips: a skipped authorization check is
indistinguishable from an absent one.
"""
import re

import pytest

import api.main as main

# Routes intentionally reachable without authentication. Each was reviewed.
PUBLIC_ALLOWLIST = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/institutions",
    "/api/stats/platform",
    "/api/stats/cancer-types",
    "/api/contact",
    "/api/marketplace/inquiry",
    "/api/marketplace/products",
    "/api/marketplace/products/{product_id}",
    "/api/diseases/variable-sets",
    "/api/diseases/{disease_name}/variables",
    "/api/consent/templates",
    "/api/docs",
    "/api/redoc",
    # FastAPI's own schema, served alongside the docs above. Describes the
    # API surface, exposes no data.
    "/api/openapi.json",
}

RESEARCH_PREFIXES = ("/api/researcher", "/api/cohort", "/api/extraction",
                     "/api/regulatory", "/api/study/")
PATIENT_PREFIXES = ("/api/patient/", "/api/studies/", "/api/consent/sign")
INSTITUTION_PREFIXES = ("/api/institution/", "/api/emr/")
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def app_routes():
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


def concrete(path):
    return re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)


def call(client, method, path, headers=None):
    return client.request(method, concrete(path), headers=headers or {}, json={})


class TestEveryRouteIsGated:
    def test_no_route_uses_a_jwt_claim_for_authorization(self):
        """The token's role claim must never decide what a request may do."""
        offenders = [
            f"{m} {p}" for m, p, src in app_routes()
            if re.search(r'token_data(?:\.get\(|\[)["\']type["\']', src)
        ]
        assert not offenders, (
            f"these handlers branch on the JWT role claim, not the database: {offenders}"
        )

    def test_no_route_uses_bare_require_auth(self):
        """require_auth validates the signature only; it does not check the row."""
        offenders = [
            f"{m} {p}" for m, p, src in app_routes()
            if "Depends(require_auth)" in src
        ]
        assert not offenders, f"ungated routes: {offenders}"

    @pytest.mark.parametrize("method,path", [
        (m, p) for m, p, _ in app_routes() if p not in PUBLIC_ALLOWLIST
    ])
    def test_protected_routes_reject_anonymous_callers(self, client, method, path):
        r = call(client, method, path)
        assert r.status_code in (401, 403, 405, 422), (
            f"{method} {path} served an anonymous caller (status {r.status_code})"
        )


class TestResearchSurface:
    ROUTES = [(m, p) for m, p, _ in app_routes()
              if p.startswith(RESEARCH_PREFIXES) and p not in PUBLIC_ALLOWLIST]

    @pytest.mark.parametrize("method,path", ROUTES)
    def test_patient_token_is_refused(self, client, patient_user, method, path):
        r = call(client, method, path, patient_user)
        assert r.status_code != 200, f"a patient reached {method} {path}"

    @pytest.mark.parametrize("method,path", ROUTES)
    def test_unapproved_researcher_is_refused(self, client, unapproved_researcher,
                                              method, path):
        r = call(client, method, path, unapproved_researcher)
        assert r.status_code != 200, f"an unapproved researcher reached {method} {path}"

    def test_approval_message_explains_the_state(self, client, unapproved_researcher):
        r = client.get("/api/researcher/studies", headers=unapproved_researcher)
        assert r.status_code == 403
        assert "pending approval" in r.json()["detail"].lower()

    def test_unverified_researcher_is_refused_even_when_approved(self, client, make_user):
        headers, _ = make_user("unverified@example.com", role="researcher",
                               verified=False, approved=True)
        r = client.get("/api/researcher/studies", headers=headers)
        assert r.status_code == 403
        detail = r.json()["detail"].lower()
        assert "identity" in detail
        # There is no email system, so the refusal must not tell someone to
        # go and check their inbox for a link that will never arrive.
        assert "verify your email" not in detail

    def test_approved_researcher_is_allowed(self, client, approved_researcher):
        assert client.get("/api/researcher/studies",
                          headers=approved_researcher).status_code == 200


class TestPatientSurface:
    ROUTES = [(m, p) for m, p, _ in app_routes() if p.startswith("/api/patient/")]

    @pytest.mark.parametrize("method,path", ROUTES)
    def test_researcher_token_is_refused(self, client, approved_researcher, method, path):
        r = call(client, method, path, approved_researcher)
        assert r.status_code != 200, f"a researcher reached {method} {path}"


class TestInstitutionSurface:
    ROUTES = [(m, p) for m, p, _ in app_routes() if p.startswith(INSTITUTION_PREFIXES)]

    @pytest.mark.parametrize("method,path", ROUTES)
    def test_patient_token_is_refused(self, client, patient_user, method, path):
        r = call(client, method, path, patient_user)
        assert r.status_code != 200, f"a patient reached {method} {path}"

    def test_institution_account_without_an_institution_is_refused(self, client, make_user):
        """An unscoped institution account could otherwise read every institution."""
        headers, _ = make_user("unscoped@example.com", role="institution",
                               verified=True, institution_id=None)
        r = client.get("/api/institution/agreements", headers=headers)
        assert r.status_code == 403
        assert "not linked" in r.json()["detail"].lower()


class TestAccountLifecycle:
    def test_deactivated_user_is_refused_everywhere(self, client, make_user):
        headers, user_id = make_user("deactivate@example.com", role="researcher",
                                     verified=True, approved=True)
        assert client.get("/api/researcher/studies", headers=headers).status_code == 200

        from api.models import User
        session = client._session_factory()
        session.query(User).filter(User.id == user_id).update({"is_active": False})
        session.commit()
        session.close()

        for path in ["/api/researcher/studies", "/api/auth/me"]:
            assert client.get(path, headers=headers).status_code == 401, (
                f"{path} still served a deactivated account"
            )

    def test_revoked_approval_takes_effect_immediately(self, client, make_user):
        headers, user_id = make_user("revoke-me@example.com", role="researcher",
                                     verified=True, approved=True)
        assert client.get("/api/researcher/studies", headers=headers).status_code == 200

        from api.models import User
        session = client._session_factory()
        session.query(User).filter(User.id == user_id).update(
            {"researcher_approved_at": None})
        session.commit()
        session.close()

        assert client.get("/api/researcher/studies", headers=headers).status_code == 403
