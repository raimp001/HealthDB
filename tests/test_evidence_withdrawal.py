from api.models import ResearchEvidence, DataAccessLog
from api.research_readiness import REQUIREMENTS
from test_site_feasibility import setup


def body(category='consent_authorization'):
    return dict(category=category, reference='PROTOCOL-v1', sha256='a'*64,
                scope='site-A.dataset-v1.research', expires_at='2099-01-01T00:00:00Z')


def test_withdrawal_blocks_replacement_until_independent_disposition(client, make_user):
    owner, member, url, _ = setup(client, make_user)
    admin, _ = make_user('reviewer@example.com', role='admin')
    path = '/api/researcher/studies/' + url.rsplit('/', 1)[-1] + '/readiness'
    ids = []
    for category in REQUIREMENTS:
        r = client.post(path, headers=owner, json=body(category)); assert r.status_code == 200
        eid = r.json()['id']; ids.append(eid)
        assert client.post(f'/api/research-evidence/{eid}/review', headers=admin, json={'decision':'verified'}).status_code == 200
    assert client.get(path, headers=owner).json()['evidence_complete']
    endpoint = f'/api/research-evidence/{ids[0]}'
    withdrawal = {'reference':'ADMIN-001', 'reason':'Institution suspended the covered scope'}
    assert client.post(endpoint+'/withdraw', json=withdrawal).status_code == 401
    assert client.post(endpoint+'/withdraw', headers=member, json=withdrawal).status_code == 403
    assert client.post(endpoint+'/withdraw', headers=owner, json={**withdrawal, 'patient_id':'forbidden'}).status_code == 422
    assert client.post(endpoint+'/withdraw', headers=owner, json=withdrawal).status_code == 200
    assert client.post(endpoint+'/withdraw', headers=owner, json=withdrawal).status_code == 409
    assert client.post(endpoint+'/review', headers=admin, json={'decision':'verified'}).status_code == 409
    replacement = client.post(path, headers=owner, json=body(next(iter(REQUIREMENTS)))).json()['id']
    assert client.post(f'/api/research-evidence/{replacement}/review', headers=admin, json={'decision':'verified'}).status_code == 200
    report = client.get(path, headers=owner)
    assert report.headers['cache-control'] == 'no-store'
    assert report.json()['open_withdrawals'] == 1
    assert not report.json()['evidence_complete']
    disposition = {**withdrawal, 'future_use':'stopped', 'recipients':'notified', 'retained_data':'retained_under_reviewed_policy'}
    assert client.post(endpoint+'/disposition', headers=owner, json=disposition).status_code == 403
    assert client.post(endpoint+'/disposition', headers=admin, json=withdrawal).status_code == 422
    assert client.post(endpoint+'/disposition', headers=admin, json=disposition).status_code == 200
    assert client.post(endpoint+'/disposition', headers=admin, json=disposition).status_code == 409
    report = client.get(path, headers=owner).json()
    assert report['open_withdrawals'] == 0
    assert report['evidence_complete']
    assert report['live_data_enabled'] is False
    old = next(x for x in report['evidence'] if x['id'] == ids[0])
    assert old['status'] == 'withdrawal_closed'
    assert [x['decision'] for x in old['review_history']] == ['verified','withdrawn','withdrawal_closed']
    with client._session_factory() as db:
        assert db.query(DataAccessLog).filter(DataAccessLog.access_type.in_(['evidence_withdrawn','evidence_withdrawal_closed'])).count() == 2


def test_admin_cannot_close_own_withdrawal_or_reactivate_old_evidence(client, make_user):
    owner, _, url, _ = setup(client, make_user)
    admin, _ = make_user('admin@example.com', role='admin')
    other, _ = make_user('other-admin@example.com', role='admin')
    path = '/api/researcher/studies/' + url.rsplit('/',1)[-1] + '/readiness'
    eid = client.post(path, headers=owner, json=body()).json()['id']
    endpoint = f'/api/research-evidence/{eid}'
    withdrawal = {'reference':'ADMIN-001','reason':'Protocol requires institutional reassessment'}
    assert client.post(endpoint+'/withdraw', headers=admin, json=withdrawal).status_code == 200
    report = client.get(path, headers=admin).json()
    assert not report['evidence'][0]['can_close_withdrawal']
    disposition = {**withdrawal,'future_use':'not_applicable','recipients':'not_applicable','retained_data':'not_applicable'}
    assert client.post(endpoint+'/disposition', headers=admin, json=disposition).status_code == 403
    assert client.post(endpoint+'/disposition', headers=other, json=disposition).status_code == 200
    assert client.post(endpoint+'/review', headers=other, json={'decision':'verified'}).status_code == 409
    assert not client.get(path, headers=owner).json()['evidence_complete']
