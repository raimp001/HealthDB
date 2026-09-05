from conftest import VALID_PASSWORD


def test_disabled_account_cannot_login_or_restore_session(client, register):
    from api.models import User
    result = register('disabled@example.com').json()
    token = result['access_token']
    with client._session_factory() as db:
        user = db.query(User).filter(User.email == 'disabled@example.com').one()
        user.is_active = False
        db.commit()
    assert client.post('/api/auth/login', json={
        'email': 'disabled@example.com', 'password': VALID_PASSWORD,
    }).status_code == 401
    assert client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401


def test_health_reports_revision_and_disables_caching(client, monkeypatch):
    monkeypatch.setenv('VERCEL_GIT_COMMIT_SHA', 'test-revision')
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['revision'] == 'test-revision'
    assert response.headers['cache-control'] == 'no-store'


def test_database_failure_is_503_without_connection_details(client):
    import api.main as main

    class UnavailableDatabase:
        def execute(self, statement):
            raise RuntimeError('postgres://secret:password@private-host/database')

    main.app.dependency_overrides[main.get_db] = lambda: UnavailableDatabase()
    response = client.get('/api/health')
    assert response.status_code == 503
    assert response.json()['database'] == 'unavailable'
    assert 'private-host' not in response.text
    assert 'password' not in response.text
