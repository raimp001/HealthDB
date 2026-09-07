from api.models import ContactSubmission, DataAccessLog


def test_admin_access_and_approval(client, make_user):
    admin, _ = make_user('admin@example.com', role='admin')
    researcher, uid = make_user('tester@example.com', verified=True)
    assert client.get('/api/admin/overview').status_code == 401
    assert client.get('/api/admin/overview', headers=researcher).status_code == 403
    path = f'/api/admin/researchers/{uid}/decision'
    assert client.post(path, headers=researcher, json={'decision': 'approve'}).status_code == 403
    assert client.post(path, headers=admin, json={'decision': 'approve'}).json()['approved']
    assert client.get('/api/admin/overview', headers=admin).headers['cache-control'] == 'no-store'
    body = client.get('/api/admin/overview', headers=admin).json()
    assert body['researchers'][0]['approved']
    assert 'password_hash' not in str(body)
    assert client.post(path, headers=admin, json={'decision': 'revoke'}).json()['approved'] is False
    with client._session_factory() as db:
        assert db.query(DataAccessLog).filter(DataAccessLog.access_type == 'researcher_revoke').count() == 1


def test_approval_does_not_bypass_identity(client, make_user):
    admin, admin_id = make_user('admin@example.com', role='admin')
    _, uid = make_user('unverified@example.com')
    assert client.post(f'/api/admin/researchers/{uid}/decision', headers=admin, json={'decision': 'approve'}).status_code == 409
    assert client.post(f'/api/admin/researchers/{admin_id}/decision', headers=admin, json={'decision': 'approve'}).status_code == 404


def test_request_status_is_separate_from_approval(client, make_user):
    admin, _ = make_user('admin@example.com', role='admin')
    with client._session_factory() as db:
        c = ContactSubmission(name='Applicant', email='new@example.com', message='Pilot request')
        db.add(c)
        db.commit()
        cid = c.id
    path = f'/api/admin/contacts/{cid}/status'
    assert client.post(path, headers=admin, json={'status': 'approved'}).status_code == 422
    assert client.post(path, headers=admin, json={'status': 'contacted'}).json() == {'status': 'contacted'}
    body = client.get('/api/admin/overview', headers=admin).json()
    assert body['contacts'][0]['status'] == 'contacted'
    assert body['researchers'] == []
