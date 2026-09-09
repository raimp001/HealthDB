import hashlib

from api.main import verify_password
from api.models import User
from conftest import VALID_PASSWORD


def test_legacy_password_requires_exact_password():
    stored = hashlib.sha256(VALID_PASSWORD.encode()).hexdigest()
    assert verify_password(VALID_PASSWORD, stored)
    assert not verify_password('incorrect', stored)
    assert not verify_password(stored, stored)
    assert not verify_password(VALID_PASSWORD, 'x' * 64)


def test_successful_login_upgrades_legacy_admin_password(client, register):
    user_id = register('legacy@example.com').json()['user']['id']
    stored = hashlib.sha256(VALID_PASSWORD.encode()).hexdigest()
    with client._session_factory() as db:
        user = db.get(User, user_id)
        user.password_hash = stored
        user.user_type = 'admin'
        db.commit()
    response = client.post('/api/auth/login', json={'email': 'legacy@example.com', 'password': 'incorrect'})
    assert response.status_code == 401
    with client._session_factory() as db:
        assert db.get(User, user_id).password_hash == stored
    response = client.post('/api/auth/login', json={'email': 'legacy@example.com', 'password': VALID_PASSWORD})
    assert response.status_code == 200
    assert response.json()['user']['user_type'] == 'admin'
    with client._session_factory() as db:
        updated = db.get(User, user_id).password_hash
        assert updated.startswith('pbkdf2_sha256$')
        assert verify_password(VALID_PASSWORD, updated)


def test_inactive_legacy_account_stays_blocked(client, register):
    user_id = register('inactive-legacy@example.com').json()['user']['id']
    stored = hashlib.sha256(VALID_PASSWORD.encode()).hexdigest()
    with client._session_factory() as db:
        user = db.get(User, user_id)
        user.password_hash = stored
        user.is_active = False
        db.commit()
    assert client.post('/api/auth/login', json={'email': 'inactive-legacy@example.com', 'password': VALID_PASSWORD}).status_code == 401
    with client._session_factory() as db:
        assert db.get(User, user_id).password_hash == stored
