from api.models import StudyCollaborator, DataAccessLog


def setup(client, make_user):
    owner, _ = make_user('owner@example.com', verified=True, approved=True)
    member, uid = make_user('member@example.com', verified=True, approved=True)
    sid = client.post('/api/workspace/projects', headers=owner, json={'name': 'Mapping pilot'}).json()['id']
    url = f'/api/workspace/projects/{sid}'
    plan = {'revision': 0, 'listed': False, 'plan': {'variables': [{'name': 'stage', 'definition': 'Stage at diagnosis'}]}}
    assert client.put(url, headers=owner, json=plan).status_code == 200
    with client._session_factory() as db:
        db.add(StudyCollaborator(study_id=sid, user_id=uid, email='member@example.com', role='co_investigator', status='accepted'))
        db.commit()
    return owner, member, url, plan


def declaration():
    return {'revision': 0, 'plan_revision': 1, 'site_label': 'Pilot site', 'mappings': [{'variable': 'stage', 'availability': 'available', 'source': 'Registry stage field'}]}


def test_team_access_and_reporter_ownership(client, make_user):
    owner, member, url, _ = setup(client, make_user)
    other, _ = make_user('other@example.com', verified=True, approved=True)
    endpoint = url + '/feasibility'
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint, headers=other).status_code == 403
    assert client.put(endpoint, headers=other, json=declaration()).status_code == 403
    assert client.put(endpoint, headers=member, json=declaration()).status_code == 200
    body = declaration(); body['revision'] = 1
    assert client.put(endpoint, headers=owner, json=body).status_code == 409
    body['user_id'] = 'another-user'
    assert client.put(endpoint, headers=member, json=body).status_code == 422
    response = client.get(endpoint, headers=owner)
    assert response.headers['cache-control'] == 'no-store'
    assert response.json()['declarations'][0]['mine'] is False
    assert client.get(endpoint, headers=member).json()['declarations'][0]['mine'] is True
    with client._session_factory() as db:
        assert db.query(DataAccessLog).filter_by(access_type='site_feasibility_saved').count() == 1


def test_versions_and_plan_changes(client, make_user):
    owner, member, url, plan = setup(client, make_user)
    endpoint = url + '/feasibility'
    assert client.put(endpoint, headers=member, json=declaration()).status_code == 200
    assert client.put(endpoint, headers=member, json=declaration()).status_code == 409
    plan['revision'] = 1
    assert client.put(url, headers=owner, json=plan).status_code == 200
    assert client.get(endpoint, headers=member).json()['declarations'][0]['stale'] is True
    body = declaration(); body['revision'] = 1
    assert client.put(endpoint, headers=member, json=body).status_code == 409
    body['plan_revision'] = 2
    assert client.put(endpoint, headers=member, json=body).json()['revision'] == 2
    assert client.get(endpoint, headers=owner).json()['declarations'][0]['stale'] is False
    assert client.put(endpoint, headers=member, json=body).status_code == 409


def test_complete_mapping_and_derivation_rules(client, make_user):
    owner, _, url, _ = setup(client, make_user)
    endpoint = url + '/feasibility'
    for mappings in ([], [{'variable': 'extra'}], [{'variable': 'stage'}] * 2,
                     [{'variable': 'stage', 'availability': 'available'}],
                     [{'variable': 'stage', 'availability': 'derivable', 'source': 'Registry'}]):
        body = declaration(); body['mappings'] = mappings
        assert client.put(endpoint, headers=owner, json=body).status_code == 422
    body = declaration(); body['mappings'][0].update(availability='derivable', transformation='Use documented stage coding rules')
    assert client.put(endpoint, headers=owner, json=body).status_code == 200
