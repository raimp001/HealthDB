"""A database problem must not become a total outage.

The startup event retried initialize_database() unguarded, while the
identical call at import was wrapped. So when initialization raised,
FastAPI's startup failed, the app refused to serve, and every route died at
the platform level as FUNCTION_INVOCATION_FAILED — including routes that
never touch the database.

Two things are lost that way. The API goes down entirely rather than
partially, and the diagnosis goes with it: /api/health is written to catch a
failed database probe and answer 503 "degraded" with the reason, and none of
that runs if the app will not start. What an operator gets instead is an
opaque platform error with no cause in it.
"""
import pytest
from fastapi.testclient import TestClient


def test_the_app_serves_when_initialization_fails(monkeypatch):
    """The whole point: a broken database is not a reason to serve nothing."""
    import api.main as main

    def explode():
        raise RuntimeError("could not connect to the database")

    monkeypatch.setattr(main, "initialize_database", explode)

    # Entering the context manager runs the startup event.
    with TestClient(main.app) as client:
        response = client.get("/api/health")
    assert response.status_code in (200, 503), response.text


def test_a_failed_probe_is_reported_as_degraded_not_as_a_crash(monkeypatch):
    """The health endpoint's own error handling has to be reachable."""
    import api.main as main

    monkeypatch.setattr(main, "initialize_database",
                        lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    with TestClient(main.app) as client:
        response = client.get("/api/health")

    # Whatever the database is doing, the answer is the application's, with a
    # status in it — not the platform's opaque failure.
    assert response.headers["content-type"].startswith("application/json")
    assert "status" in response.json()


def test_the_failure_is_recorded_rather_than_swallowed_silently(monkeypatch, capsys):
    """Serving through a failure must not mean hiding it."""
    import api.main as main

    monkeypatch.setattr(main, "initialize_database",
                        lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    with TestClient(main.app):
        pass

    assert "Database initialization failed at startup" in capsys.readouterr().out


def test_a_healthy_startup_still_initializes(monkeypatch):
    """The guard must not turn initialization into a no-op."""
    import api.main as main

    calls = []
    monkeypatch.setattr(main, "initialize_database", lambda: calls.append(1))

    with TestClient(main.app):
        pass
    assert calls, "startup no longer initializes the database"
