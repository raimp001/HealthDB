from test_site_feasibility import setup
from api.models import WorkContributionEvent

WORK = {'title': 'Dictionary review', 'description': 'Reviewed variable definitions and units', 'evidence_ref': 'Protocol revision 1', 'minutes': 60}


def test_ledger_review_dispute_and_immutable_history(client, make_user):
    owner, member, url, _ = setup(client, make_user)
    endpoint = url + '/contributions'
    r = client.post(endpoint, headers=member, json=WORK)
    assert r.status_code == 201
    eid = r.json()['id']; action = endpoint + f'/{eid}/events'
    decision = {'revision': 1, 'action': 'accepted', 'reason': 'Definitions checked against protocol'}
    assert client.post(action, headers=member, json=decision).status_code == 403
    assert client.post(action, headers=owner, json=decision).status_code == 200
    assert client.post(action, headers=owner, json=decision).status_code == 409
    decision.update(revision=2, action='disputed', reason='Please also credit the coding review')
    assert client.post(action, headers=owner, json=decision).status_code == 403
    assert client.post(action, headers=member, json=decision).status_code == 200
    decision.update(revision=3, action='accepted', reason='Additional coding review acknowledged', policy_ref='Work policy revision 1')
    assert client.post(action, headers=owner, json=decision).status_code == 200
    response = client.get(endpoint, headers=member)
    assert response.headers['cache-control'] == 'no-store'
    row = response.json()['items'][0]
    assert [e['action'] for e in row['events']] == ['submitted', 'accepted', 'disputed', 'accepted']
    assert row['events'][0]['content'] == WORK
    assert row['revision'] == 4
    with client._session_factory() as db:
        assert db.query(WorkContributionEvent).filter_by(contribution_id=eid).count() == 4
    assert client.delete(action, headers=owner).status_code == 405


def test_ledger_access_self_approval_and_validation(client, make_user):
    owner, member, url, _ = setup(client, make_user)
    other, _ = make_user('other@example.com', verified=True, approved=True)
    endpoint = url + '/contributions'
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint, headers=other).status_code == 403
    assert client.post(endpoint, headers=other, json=WORK).status_code == 403
    assert client.post(endpoint, headers=owner, json={**WORK, 'payment': 100}).status_code == 422
    eid = client.post(endpoint, headers=owner, json=WORK).json()['id']
    action = endpoint + f'/{eid}/events'
    decision = {'revision': 1, 'action': 'accepted', 'reason': 'Attempting to approve own work'}
    assert client.post(action, headers=owner, json=decision).status_code == 403
    assert client.post(action, headers=member, json=decision).status_code == 403
    decision['action'] = 'resubmitted'
    assert client.post(action, headers=owner, json=decision).status_code == 409


def test_ledger_changes_and_resubmission(client, make_user):
    owner, member, url, _ = setup(client, make_user)
    endpoint = url + '/contributions'
    eid = client.post(endpoint, headers=member, json=WORK).json()['id']
    action = endpoint + f'/{eid}/events'
    decision = {'revision': 1, 'action': 'changes_requested', 'reason': 'Please clarify measurement units'}
    assert client.post(action, headers=owner, json=decision).status_code == 200
    decision.update(revision=2, action='resubmitted', reason='Units clarified in protocol revision 2')
    assert client.post(action, headers=member, json=decision).status_code == 200
    assert client.get(endpoint, headers=owner).json()['items'][0]['status'] == 'resubmitted'
