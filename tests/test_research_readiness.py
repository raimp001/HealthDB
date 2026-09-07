from datetime import datetime, timedelta
from api.models import Study, ResearchEvidence
from api.research_readiness import REQUIREMENTS


def test_evidence_review_and_revocation(client, make_user):
    owner, owner_id = make_user('owner@fixture.com', verified=True, approved=True)
    reviewer, _ = make_user('reviewer@fixture.com', role='admin', verified=True)
    stranger, _ = make_user('stranger@fixture.com', verified=True, approved=True)
    unapproved, _ = make_user('pending@fixture.com')
    with client._session_factory() as db:
        study = Study(user_id=owner_id, name='Readiness fixture')
        db.add(study); db.commit(); sid = study.id
    path = f'/api/researcher/studies/{sid}/readiness'
    assert client.get(path, headers=stranger).status_code == 403
    assert client.get(path, headers=unapproved).status_code == 403
    assert client.get(path, headers=owner).json()['evidence_complete'] is False
    ids = []
    for category in REQUIREMENTS:
        body = dict(category=category, reference='DOC-001', sha256='a'*64,
                    scope='site-A.dataset-v1.recipient-B.research', expires_at='2099-01-01T00:00:00Z')
        created = client.post(path, json=body, headers=owner)
        assert created.status_code == 200, created.text
        eid = created.json()['id']; ids.append(eid)
        review = f'/api/research-evidence/{eid}/review'
        assert client.post(review, json={'decision': 'verified'}, headers=owner).status_code == 403
        assert client.post(review, json={'decision': 'verified'}, headers=reviewer).status_code == 200
        assert client.post(review, json={'decision': 'verified'}, headers=reviewer).status_code == 409
    report = client.get(path, headers=owner).json()
    assert report['evidence_complete'] is True
    assert report['live_data_enabled'] is False
    review = f'/api/research-evidence/{ids[0]}/review'
    assert client.post(review, json={'decision': 'revoked'}, headers=reviewer).status_code == 200
    report = client.get(path, headers=owner).json()
    assert report['evidence_complete'] is False
    row = next(r for r in report['evidence'] if r['id'] == ids[0])
    assert [r['decision'] for r in row['review_history']] == ['verified', 'revoked']
    body['expires_at'] = '2000-01-01T00:00:00Z'
    assert client.post(path, json=body, headers=owner).status_code == 422


def test_latest_version_and_scope_prevent_false_readiness():
    from api.research_readiness import readiness_report
    now = datetime.utcnow()
    rows = [ResearchEvidence(id=str(i), category=c, scope='dataset-v1', status='verified',
                            expires_at=now+timedelta(days=1), created_at=now)
            for i, c in enumerate(REQUIREMENTS)]
    assert readiness_report(rows)['evidence_complete']
    rows[0].scope = 'dataset-v2'
    assert not readiness_report(rows)['evidence_complete']
    rows[0].scope = 'dataset-v1'
    rows.append(ResearchEvidence(id='new', category=rows[0].category, scope='dataset-v1', status='rejected',
                                expires_at=now+timedelta(days=1), created_at=now+timedelta(seconds=1)))
    assert not readiness_report(rows)['evidence_complete']
    rows.pop(); rows[0].expires_at = now-timedelta(days=1)
    assert not readiness_report(rows)['evidence_complete']
