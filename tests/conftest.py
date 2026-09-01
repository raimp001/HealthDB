"""Shared fixtures. Every test runs against a disposable SQLite database so
nothing ever touches the real data/healthdb.db."""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["JWT_SECRET"] = "test-only-secret-not-used-anywhere-else"
os.environ["ENVIRONMENT"] = "test"
# The pilot gate is off by default; most tests need to create accounts.
# tests/test_pilot_gate.py covers the gate itself.
os.environ["ALLOW_SELF_SERVICE_REGISTRATION"] = "true"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import api.main as main
    from api.models import Base

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    with TestClient(main.app) as c:
        c._session_factory = TestingSession
        yield c
    main.app.dependency_overrides.clear()
    engine.dispose()
    os.unlink(path)


VALID_PASSWORD = "Str0ng!Passw0rd#2026"


@pytest.fixture()
def register(client):
    def _register(email, user_type="researcher", password=VALID_PASSWORD, name="Test User"):
        return client.post("/api/auth/register", json={
            "email": email, "password": password, "name": name, "user_type": user_type,
        })
    return _register
