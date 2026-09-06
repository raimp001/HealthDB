"""Public, deterministic fixtures. No database reads, writes, or patient records."""
from datetime import date
from types import SimpleNamespace
from fastapi import APIRouter
from .cohort_query import CohortCriteria, matching_patient_ids

router = APIRouter()


def demo_records():
    records = []
    for i in range(24):
        diagnosis, code = [('Multiple Myeloma', 'C90.0'), ('DLBCL', 'C83.3'), ('AML', 'C92.0')][i % 3]
        rows = [
            ('diagnosis', {'display': diagnosis, 'code': code, 'stage': ['I', 'II', 'III', 'IV'][i % 4]}),
            ('demographics', {'age': 30 + i * 2, 'sex': 'Female' if i % 2 else 'Male'}),
            ('treatment', {'treatment_type': 'Chemotherapy', 'line_of_therapy': 1 + i % 3}),
            ('outcome', {'response': 'CR' if i % 2 else 'PR', 'follow_up_months': 6 + i}),
        ]
        for category, data in rows:
            records.append(SimpleNamespace(patient_id=f'synthetic-{i + 1:02}', data_category=category,
                                           deidentified_data=data, original_date=date(2024, 1, 1)))
    return records


@router.post('/api/demo/cohort/build', tags=['Public demo'])
def build_demo(criteria: CohortCriteria):
    """Evaluate filters against 24 fictional profiles; never queries the database.

    These deliberately simplified fixtures do not represent clinical staging,
    treatment recommendations, real patients, or product adoption.
    """
    records = demo_records()
    ids = matching_patient_ids(records, criteria)
    return {
        'mode': 'synthetic_demo', 'fixture_version': '1', 'total_profiles': 24,
        'patient_count': len(ids),
        'data_points': sum(str(r.patient_id) in ids for r in records),
        'criteria': criteria.model_dump(mode='json'),
        'limitations': 'Fictional workflow fixtures only. No real patient data or clinical inference.',
    }


@router.get('/api/capabilities', tags=['Public demo'])
def capabilities():
    return {
        'product': 'HealthDB', 'stage': 'synthetic-data pilot',
        'public_demo': {'method': 'POST', 'path': '/api/demo/cohort/build', 'authentication': 'none'},
        'schema': '/api/openapi.json', 'documentation': '/developers',
        'agent_guide': '/llms.txt',
        'private_access': 'Invited accounts; Bearer token and role checks required.',
        'export': {'formats': ['csv'], 'requires': ['selected variables', 'current approvals', 'eligible consented records']},
        'real_patient_data_supported': False,
    }
