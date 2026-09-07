import pytest
from api.models import Study


@pytest.mark.parametrize('decision', ['accept', 'decline'])
def test_invitation_requires_recipient_consent(client, register, decision):
    owner = register('owner@example.com').json()
    recipient = register('recipient@example.com').json()
    stranger = register('stranger@example.com').json()
    headers = lambda user: {'Authorization': 'Bearer ' + user['access_token']}
    with client._session_factory() as db:
        study = Study(user_id=owner['user']['id'], name='Synthetic research study')
        db.add(study)
        db.commit()
        study_id = study.id
    path = f'/api/study/{study_id}'
    response = client.post(path + '/invite', params={'email': 'recipient@example.com', 'role': 'analyst'}, headers=headers(owner))
    assert response.status_code == 200
    assert response.json()['status'] == 'invited'
    assert 'No email was sent' in response.json()['message']
    invitation_id = response.json()['collaborator_id']
    assert client.get(path + '/team', headers=headers(recipient)).status_code == 403
    assert len(client.get('/api/researcher/invitations', headers=headers(recipient)).json()) == 1
    respond = f'/api/researcher/invitations/{invitation_id}/respond'
    assert client.post(respond, params={'decision': decision}, headers=headers(stranger)).status_code == 404
    assert client.post(respond, params={'decision': decision}, headers=headers(recipient)).status_code == 200
    assert client.post(respond, params={'decision': decision}, headers=headers(recipient)).status_code == 409
    assert client.get(path + '/team', headers=headers(recipient)).status_code == (200 if decision == 'accept' else 403)
    assert client.get('/api/researcher/invitations', headers=headers(recipient)).json() == []
    assert client.post(path + '/invite', params={'email': 'owner@example.com', 'role': 'analyst'}, headers=headers(owner)).status_code == 400
    assert client.post(path + '/invite', params={'email': 'new@example.com', 'role': 'admin'}, headers=headers(owner)).status_code == 422
