from api.models import ResearchPlan, StudyCollaborator


def create(client, headers):
    r = client.post('/api/workspace/projects', headers=headers, json={'name': 'Outcomes pilot'})
    assert r.status_code == 201, r.text
    return r.json()['id']


def plan(listed=False, revision=0):
    return {'revision': revision, 'listed': listed, 'plan': {
        'question': 'How do outcomes differ between exposure groups?',
        'population': 'Adults in the synthetic cohort', 'outcome': 'Overall survival definition',
        'seeking': 'Statistician', 'variables': [{'name': 'stage', 'definition': 'Stage at diagnosis'}],
        'milestones': [{'title': 'Review protocol', 'owner': 'PI', 'status': 'todo'}]}}


def test_plan_revision_and_private_boundary(client, make_user):
    owner, _ = make_user('owner@example.com', verified=True, approved=True)
    other, _ = make_user('other@example.com', verified=True, approved=True)
    sid = create(client, owner)
    url = f'/api/workspace/projects/{sid}'
    assert client.get(url, headers=other).status_code == 403
    assert client.put(url, headers=owner, json=plan()).status_code == 200
    assert client.put(url, headers=owner, json=plan()).status_code == 409
    assert client.put(url, headers=owner, json=plan(revision=1)).status_code == 200
    assert client.put(url, headers=owner, json=plan(revision=1)).status_code == 409
    r = client.get(url, headers=owner)
    assert r.json()['revision'] == 2
    assert r.headers['cache-control'] == 'no-store'
    assert client.get('/api/workspace/opportunities', headers=other).json()['items'] == []


def test_discovery_request_invite_accept_and_team_discussion(client, make_user):
    owner, _ = make_user('owner@example.com', verified=True, approved=True)
    other, uid = make_user('other@example.com', verified=True, approved=True)
    sid = create(client, owner)
    url = f'/api/workspace/projects/{sid}'
    assert client.put(url, headers=owner, json=plan(True)).status_code == 200
    listed = client.get('/api/workspace/opportunities', headers=other).json()['items'][0]
    assert set(listed) == {'id', 'name', 'question', 'seeking', 'mine'}
    assert 'variables' not in listed
    interest = f'/api/workspace/opportunities/{sid}/interest'
    assert client.post(interest, headers=other, json={'message': 'I can help with analysis.'}).status_code == 201
    assert client.post(interest, headers=other, json={'message': 'Duplicate request test'}).status_code == 409
    assert client.get(url, headers=other).status_code == 403
    requests = client.get(url + '/interests', headers=owner).json()
    decision = url + '/interests/' + requests[0]['id']
    assert client.post(decision, headers=other, json={'decision': 'invite'}).status_code == 403
    assert client.post(decision, headers=owner, json={'decision': 'invite'}).status_code == 200
    assert client.get(url, headers=other).status_code == 403
    with client._session_factory() as db:
        invite = db.query(StudyCollaborator).filter_by(study_id=sid, user_id=uid).one().id
    assert client.post(f'/api/researcher/invitations/{invite}/respond?decision=accept', headers=other).status_code == 200
    assert client.get(url, headers=other).status_code == 200
    assert not client.get(url, headers=other).json()['can_edit']
    assert client.put(url, headers=other, json=plan(revision=1)).status_code == 403
    assert client.post(url + '/discussion', headers=other, json={'message': 'Please define the censoring rules.'}).status_code == 201
    assert len(client.get(url + '/discussion', headers=owner).json()) == 1
    assert client.put(url, headers=owner, json=plan(False, 1)).status_code == 200
    assert client.get('/api/workspace/opportunities', headers=other).json()['items'] == []


def test_definition_validation(client, make_user):
    owner, _ = make_user('owner@example.com', verified=True, approved=True)
    url = '/api/workspace/projects/' + create(client, owner)
    data = plan(); data['plan']['variables'] *= 2
    assert client.put(url, headers=owner, json=data).status_code == 422
    data = plan(); data['plan']['patient_records'] = []
    assert client.put(url, headers=owner, json=data).status_code == 422
    assert client.put(url, headers=owner, json={'revision': 0, 'listed': True, 'plan': {}}).status_code == 422


def test_admin_can_plan_without_weakening_researcher_gate(client, make_user):
    admin, _ = make_user('admin@example.com', role='admin')
    unapproved, _ = make_user('new@example.com', verified=True)
    assert create(client, admin)
    assert client.get('/api/workspace/projects', headers=unapproved).status_code == 403
