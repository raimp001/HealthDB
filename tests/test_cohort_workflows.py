from datetime import date, datetime, timedelta
from types import SimpleNamespace
import csv
import io
import json
import pytest
from api.cohort_query import CohortCriteria, matching_patient_ids


def record(pid='one', category='diagnosis', **data):
    return SimpleNamespace(patient_id=pid, data_category=category, deidentified_data=data, original_date=date(2024, 1, 1))


def test_exact_stage_and_conservative_age_band():
    records = [record(stage='Stage II'), record('two', stage='Stage I'),
               record('one', 'demographics', age_band='60-69'), record('two', 'demographics', age=65)]
    assert matching_patient_ids(records, CohortCriteria(stages=['I'])) == {'two'}
    assert matching_patient_ids(records, CohortCriteria(age_min=65)) == {'two'}
    assert matching_patient_ids(records, CohortCriteria(age_min=60, age_max=70)) == {'one', 'two'}


def test_exclusion_disabled_rules_and_missing_negative_findings():
    records = [record(display='AML', code='C92.0'), record('two', display='DLBCL'),
               record('two', 'outcome', mrd='Positive')]
    criteria = CohortCriteria(exclusions=[{'field': 'diagnosis', 'operator': 'IS', 'value': 'AML (C92.0)'}])
    assert matching_patient_ids(records, criteria) == {'two'}
    criteria.exclusions[0].enabled = False
    assert matching_patient_ids(records, criteria) == {'one', 'two'}
    criteria = CohortCriteria(inclusions=[{'field': 'mrd', 'operator': 'IS NOT', 'value': 'Negative'}])
    assert matching_patient_ids(records, criteria) == {'two'}


def test_followup_and_diagnosis_date_filters():
    records = [record(), record(category='outcome', follow_up_months=12)]
    assert matching_patient_ids(records, CohortCriteria(min_follow_up_months=13)) == set()
    assert matching_patient_ids(records, CohortCriteria(diagnosis_date_start=date(2025, 1, 1))) == set()


@pytest.mark.parametrize('criteria', [{'ageMin': 50}, {'age_min': 90, 'age_max': 20},
    {'inclusions': [{'field': 'response', 'operator': 'AT LEAST', 'value': 'CR'}]}])
def test_unsupported_or_invalid_filters_rejected(client, criteria):
    assert client.post('/api/demo/cohort/build', json=criteria).status_code == 422


def test_demo_is_public_deterministic_and_does_not_query_database(client, monkeypatch):
    from sqlalchemy.orm import Session
    def fail(*args, **kwargs):
        raise AssertionError('The public demo must not access the database')
    monkeypatch.setattr(Session, 'query', fail)
    response = client.post('/api/demo/cohort/build', json={'cancer_types': ['Multiple Myeloma'], 'age_min': 50})
    assert response.status_code == 200
    assert response.json()['patient_count'] == 4
    assert response.json()['data_points'] == 16
    assert response.json()['mode'] == 'synthetic_demo'
    assert '/api/demo/cohort/build' in client.get('/api/openapi.json').json()['paths']


def test_health_database_failure_is_503_without_secret(client):
    import api.main as main
    class BrokenDB:
        def execute(self, *args):
            raise RuntimeError('postgres://secret-password@example/db')
    main.app.dependency_overrides[main.get_db] = lambda: BrokenDB()
    response = client.get('/api/health')
    assert response.status_code == 503
    assert response.json()['database'] == 'unavailable'
    assert 'secret-password' not in response.text
    assert response.headers['cache-control'] == 'no-store'


def test_saved_cohort_contract_and_ownership(client, register):
    # Both are approved: this test is about cohort ownership, so it must get
    # past the researcher-approval gate to reach the behaviour it names.
    from tests.conftest import approve_researcher
    owner_body = register('cohort-owner@example.com').json()
    intruder_body = register('cohort-other@example.com').json()
    approve_researcher(client, owner_body['user']['id'])
    approve_researcher(client, intruder_body['user']['id'])
    owner = owner_body['access_token']
    intruder = intruder_body['access_token']
    headers = {'Authorization': f'Bearer {owner}'}
    criteria = {'stages': ['I'], 'age_min': 50}
    preview = client.post('/api/cohort/build', headers=headers, json=criteria)
    saved = client.post('/api/cohort/save', headers=headers, json={'name': 'Test cohort', 'criteria': criteria})
    assert preview.status_code == saved.status_code == 200
    assert saved.json()['patient_count'] == preview.json()['patient_count']
    cohort_id = saved.json()['id']
    denied = client.post('/api/researcher/studies', headers={'Authorization': f'Bearer {intruder}'},
                         json={'name': 'Wrong owner', 'cohort_id': cohort_id})
    assert denied.status_code == 404


def test_export_projection_and_consent_revocation(client, register, monkeypatch):
    import api.main as main
    from api.models import PatientProfile, Consent, ExtractedMedicalData, StudyEnrollment, RegulatorySubmission
    monkeypatch.setattr(main, 'MIN_AGGREGATE_CELL_SIZE', 1)
    from tests.conftest import approve_researcher
    owner_body = register('export-owner@example.com').json()
    approve_researcher(client, owner_body['user']['id'])
    token = owner_body['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    created = client.post('/api/researcher/studies', headers=headers, json={'name': 'Synthetic export'})
    assert created.status_code == 200
    study_id = created.json()['id']
    with client._session_factory() as db:
        patient = PatientProfile()
        db.add(patient); db.flush()
        patient_id = patient.id
        db.add_all([
            Consent(patient_id=patient.id, consent_type='research_data_sharing', status='active'),
            StudyEnrollment(study_id=study_id, patient_id=patient.id, status='enrolled'),
            ExtractedMedicalData(patient_id=patient.id, connection_id='synthetic-connection',
                data_category='diagnosis', deidentified_data={'stage': 'II', 'display': 'NOT_SELECTED'}),
            RegulatorySubmission(study_id=study_id, document_type='irb_protocol', status='approved'),
            RegulatorySubmission(study_id=study_id, document_type='dua', status='signed'),
        ])
        db.commit()
    response = client.post('/api/extraction/create', headers=headers, json={
        'study_id': study_id, 'variables': ['diagnosis.stage'], 'output_format': 'csv', 'deidentification_level': 'limited_dataset'})
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'completed', response.text
    url = f"/api/extraction/jobs/{response.json()['job_id']}/download"
    download = client.get(url, headers=headers)
    assert download.status_code == 200
    rows = list(csv.DictReader(io.StringIO(download.text)))
    assert json.loads(rows[0]['data_json']) == {'stage': 'II'}
    assert 'NOT_SELECTED' not in download.text
    with client._session_factory() as db:
        db.query(Consent).filter_by(patient_id=patient_id).update({'status': 'revoked'})
        db.commit()
    assert client.get(url, headers=headers).status_code == 410


def test_expired_or_site_only_approval_does_not_authorize_export(client):
    from api.main import require_current_export_approvals
    from api.models import RegulatorySubmission
    from fastapi import HTTPException
    with client._session_factory() as db:
        db.add_all([
            RegulatorySubmission(study_id='study', document_type='irb_protocol', status='approved',
                                 expires_at=datetime.now() - timedelta(days=1)),
            RegulatorySubmission(study_id='study', document_type='dua', status='signed'),
            RegulatorySubmission(study_id='study', institution_id='site', document_type='irb_protocol', status='approved'),
        ])
        db.commit()
        with pytest.raises(HTTPException) as caught:
            require_current_export_approvals(db, 'study')
        assert caught.value.status_code == 400
