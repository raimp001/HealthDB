"""The public trust surface: no real organisation names, no uncertified claims.

GET /api/institutions is public and unauthenticated. An earlier seeder planted
eight real hospitals there, so anyone reading the endpoint saw Stanford, Mayo,
MD Anderson and others presented as HealthDB institutions.
"""
import pytest

from api.models import Institution, User, RegulatorySubmission

REAL_ORGANISATIONS = [
    "Stanford Cancer Center", "Mayo Clinic", "MD Anderson Cancer Center",
    "Memorial Sloan Kettering", "Dana-Farber Cancer Institute",
    "Fred Hutchinson Cancer Center", "Cleveland Clinic", "Johns Hopkins Hospital",
    "OHSU Knight Cancer Institute", "Emory Winship Cancer Institute",
    "UCSF Helen Diller Cancer Center",
]


def seed(client, names):
    session = client._session_factory()
    for name in names:
        session.add(Institution(name=name, type="Academic Medical Center"))
    session.commit()
    session.close()


class TestPlaceholderInstitutionCleanup:
    def test_real_organisation_names_are_removed_on_boot(self, client):
        from api.main import remove_placeholder_institutions
        seed(client, REAL_ORGANISATIONS)

        session = client._session_factory()
        assert session.query(Institution).count() == len(REAL_ORGANISATIONS)
        removed = remove_placeholder_institutions(session)
        session.close()
        assert removed == len(REAL_ORGANISATIONS)

        body = client.get("/api/institutions").json()
        served = " ".join(i["name"] for i in body)
        for name in REAL_ORGANISATIONS:
            assert name not in served, f"{name!r} is still served publicly"

    def test_a_referenced_institution_is_kept_not_silently_deleted(self, client, register):
        """Deleting a row something points at would lose real data."""
        from api.main import remove_placeholder_institutions
        seed(client, ["Mayo Clinic"])

        session = client._session_factory()
        inst = session.query(Institution).filter(Institution.name == "Mayo Clinic").first()
        body = register("linked@example.com", user_type="researcher").json()
        session.query(User).filter(User.id == body["user"]["id"]).update(
            {"institution_id": inst.id})
        session.commit()
        remove_placeholder_institutions(session)
        session.close()

        session = client._session_factory()
        assert session.query(Institution).filter(
            Institution.name == "Mayo Clinic").count() == 1, (
            "a referenced institution was deleted rather than reported"
        )
        session.close()

    def test_cleanup_is_idempotent(self, client):
        from api.main import remove_placeholder_institutions
        seed(client, ["Cleveland Clinic"])
        session = client._session_factory()
        remove_placeholder_institutions(session)
        remove_placeholder_institutions(session)  # must not raise
        session.close()
        body = client.get("/api/institutions").json()
        assert "Cleveland Clinic" not in " ".join(i["name"] for i in body)


class TestPublicClaims:
    @pytest.mark.parametrize("path", ["src/pages/About.js", "src/pages/RepoAnalyzer.js"])
    def test_no_page_asserts_safe_harbor_as_achieved(self, path):
        """The pipeline is Safe Harbor-oriented; no statistician has reviewed it.

        It performs no named-entity recognition, so a name written into free
        text can survive. Describing it as Safe Harbor de-identification
        claims a standard the implementation has not been measured against.
        """
        source = open(path).read()
        assert "Safe Harbor de-identification" not in source, (
            f"{path} asserts Safe Harbor de-identification as achieved"
        )


class TestUnknownRoutesReturn404:
    def test_vercel_config_has_no_catch_all_rewrite(self):
        """A catch-all makes every unknown URL answer 200 with the app shell."""
        import json
        config = json.load(open("vercel.json"))
        catch_alls = [r for r in config.get("rewrites", []) if r["source"] == "/(.*)"]
        assert not catch_alls, (
            "a catch-all rewrite is present, so unknown URLs will return 200"
        )

    def test_every_app_route_is_rewritten(self):
        """A route missing from the config would 404 for a real page."""
        import json, re
        app = open("src/App.js").read()
        routes = {m for m in re.findall(r'<Route\s+path="([^"*]+)"', app)}
        configured = {r["source"] for r in json.load(open("vercel.json"))["rewrites"]}
        missing = routes - configured
        assert not missing, f"real routes absent from vercel.json: {sorted(missing)}"
