"""Health check behaviour.

The check previously returned HTTP 200 with status "degraded" when the
database was unreachable, so a load balancer or uptime monitor treated a
fully broken deployment as healthy. It also interpolated the driver exception
into the public response body.
"""
from unittest.mock import patch


class TestHealthy:
    def test_returns_200_when_the_database_is_reachable(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"


class TestUnavailable:
    def test_returns_503_when_the_database_dependency_fails(self, client):
        import api.main as main
        with patch.object(main, "SessionLocal", side_effect=RuntimeError("connection refused")):
            r = client.get("/api/health")
        assert r.status_code == 503, (
            f"a broken database returned {r.status_code}; monitors would not page"
        )
        assert r.json()["database"] == "unavailable"

    def test_does_not_leak_the_exception_to_the_caller(self, client):
        """A driver error can carry the host, port, user or connection string."""
        secret = "postgres://admin:hunter2@db.internal:5432/healthdb"
        import api.main as main
        with patch.object(main, "SessionLocal", side_effect=RuntimeError(secret)):
            r = client.get("/api/health")
        assert secret not in r.text
        for fragment in ["hunter2", "db.internal", "5432", "admin", "postgres://"]:
            assert fragment not in r.text, f"{fragment!r} leaked into the health response"
        assert r.json()["database"] == "unavailable"

    def test_logs_the_detail_server_side(self, client, caplog):
        import logging
        import api.main as main
        with caplog.at_level(logging.ERROR):
            with patch.object(main, "SessionLocal", side_effect=RuntimeError("connection refused")):
                client.get("/api/health")
        assert "connection refused" in caplog.text, (
            "the detail must still reach the server log for operators"
        )
