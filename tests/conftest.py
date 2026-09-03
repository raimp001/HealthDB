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


# ---------------------------------------------------------------------------
# Role fixtures.
#
# Privileged roles and researcher approval have no HTTP path by design, so
# tests set them the way api/manage.py does: directly on the user row.
# ---------------------------------------------------------------------------

def _set_user_fields(client, user_id, **fields):
    from api.models import User
    session = client._session_factory()
    session.query(User).filter(User.id == user_id).update(fields)
    session.commit()
    session.close()


@pytest.fixture()
def make_user(client, register):
    """Create a user in any state and return (headers, user_id)."""
    from datetime import datetime

    def _make(email, role="researcher", verified=False, approved=False,
              active=True, institution_id=None):
        signup_role = role if role in ("patient", "researcher") else "researcher"
        body = register(email, user_type=signup_role).json()
        user_id = body["user"]["id"]

        fields = {}
        if role not in ("patient", "researcher"):
            fields["user_type"] = role
        if verified:
            fields["is_verified"] = True
        if approved:
            fields["researcher_approved_at"] = datetime.utcnow()
        if not active:
            fields["is_active"] = False
        if institution_id is not None:
            fields["institution_id"] = institution_id
        if fields:
            _set_user_fields(client, user_id, **fields)

        return {"Authorization": f"Bearer {body['access_token']}"}, user_id
    return _make


@pytest.fixture()
def approved_researcher(make_user):
    headers, _ = make_user("approved@example.com", role="researcher",
                           verified=True, approved=True)
    return headers


@pytest.fixture()
def unapproved_researcher(make_user):
    headers, _ = make_user("unapproved@example.com", role="researcher",
                           verified=True, approved=False)
    return headers


@pytest.fixture()
def patient_user(make_user):
    headers, _ = make_user("patient@example.com", role="patient")
    return headers


@pytest.fixture()
def institution_user(client, make_user):
    from api.models import Institution
    session = client._session_factory()
    inst = Institution(name="Test Institution (fixture)", type="Academic Medical Center")
    session.add(inst)
    session.commit()
    inst_id = inst.id
    session.close()
    headers, _ = make_user("institution@example.com", role="institution",
                           verified=True, institution_id=inst_id)
    return headers, inst_id
