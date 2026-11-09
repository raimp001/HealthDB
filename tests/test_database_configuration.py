"""A missing DATABASE_URL must not take the whole API down, or invent a database.

healthdb.ai returned FUNCTION_INVOCATION_FAILED on every /api route while
the static site served. api/database.py fell straight through to a local
SQLite file when DATABASE_URL was unset, and on a read-only serverless
filesystem `data_dir.mkdir()` raised while the module was still being
imported — before the app existed, before any try/except, before
/api/health could report anything.

The second failure is the one that would have been worse had the directory
been writable: a production API quietly serving an empty per-instance SQLite
file in place of the real database. Each cold start gets its own. Patients'
records would appear to have vanished, and consent and access logs would be
written somewhere nobody reads. For a platform whose promise is that someone
can see where their data went, inventing a throwaway database is worse than
refusing to serve.
"""
import importlib
import sys

import pytest


def reload_database(monkeypatch, **env):
    """Re-import api.database under a given environment."""
    for key in ("DATABASE_URL", "ENVIRONMENT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("api.database", None)
    return importlib.import_module("api.database")


def test_production_without_a_url_still_imports(monkeypatch):
    """Importing is what the whole API depends on; it must not raise."""
    module = reload_database(monkeypatch, ENVIRONMENT="production")
    assert module.DATABASE_CONFIG_ERROR is not None


def test_production_without_a_url_does_not_invent_a_database(monkeypatch):
    """Serving an empty local file in place of the real one hides every record."""
    module = reload_database(monkeypatch, ENVIRONMENT="production")
    assert not module.is_sqlite
    assert module.DATABASE_URL is None
    # And no engine is built: handing create_engine a placeholder URL would
    # load that URL's driver immediately, which is the same import-time
    # failure in a new costume.
    assert module.engine is None


def test_the_reason_says_what_is_wrong(monkeypatch):
    module = reload_database(monkeypatch, ENVIRONMENT="production")
    assert "DATABASE_URL is not set" in module.DATABASE_CONFIG_ERROR


def test_the_reason_carries_no_credentials(monkeypatch):
    """It is read by whoever is debugging, and may be read by anyone."""
    module = reload_database(monkeypatch, ENVIRONMENT="production")
    reason = module.DATABASE_CONFIG_ERROR.lower()
    for secret in ("password", "@", "://", "postgres://", "postgresql://"):
        assert secret not in reason, f"reason leaks {secret!r}: {reason}"


def test_development_still_gets_its_convenience_database(monkeypatch):
    module = reload_database(monkeypatch)
    assert module.is_sqlite
    assert module.DATABASE_CONFIG_ERROR is None


def test_a_configured_url_is_used_unchanged(monkeypatch):
    url = "postgresql+psycopg2://host/db"
    module = reload_database(monkeypatch, ENVIRONMENT="production",
                             DATABASE_URL=url)
    assert module.DATABASE_URL == url
    assert module.DATABASE_CONFIG_ERROR is None
    assert module.engine is not None


def test_the_health_check_reports_the_reason(monkeypatch):
    """The point of surviving import is that something can say what broke."""
    import api.main as main
    from fastapi.testclient import TestClient

    def explode(*args, **kwargs):
        raise RuntimeError("no database")

    monkeypatch.setattr(main, "initialize_database", lambda: None)
    with TestClient(main.app) as client:
        monkeypatch.setattr(main, "text", explode)
        response = client.get("/api/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unavailable"
    assert body["reason"], "a degraded health check must say why"


@pytest.fixture(autouse=True)
def restore_database_module():
    """Leave api.database as the rest of the suite expects to find it."""
    yield
    sys.modules.pop("api.database", None)
    importlib.import_module("api.database")
