"""Evidence completeness is not authorization, certification or legal execution."""
from datetime import datetime

REQUIREMENTS = {
    'ehr_validation': 'Institution-approved FHIR connection and mapping validation',
    'deidentification': 'Dataset-specific de-identification review',
    'institution_agreement': 'Executed institution data-sharing agreement',
    'research_authority': 'Applicable research review and legal authority',
    'data_license': 'Executed dataset license with permitted uses and recipients',
    'security_review': 'Security, retention and incident-response review',
    'consent_authorization': 'Study-specific consent and authorization process review',
    'withdrawal_procedure': 'Withdrawal, recipient notification and retention procedure',
}


def readiness_report(rows):
    now = datetime.utcnow()
    requirements = []
    scopes = []
    for category, title in REQUIREMENTS.items():
        # The latest version for a category/scope supersedes older evidence,
        # including when that latest version is rejected or revoked.
        latest = {}
        for row in sorted(rows, key=lambda r: (r.created_at, r.id), reverse=True):
            if row.category == category:
                latest.setdefault(row.scope, row)
        current = [r for r in latest.values() if r.status == 'verified' and r.expires_at > now]
        scopes.append({r.scope for r in current})
        requirements.append({'category': category, 'title': title, 'evidence_current': bool(current)})
    open_withdrawals = [r for r in rows if r.status == 'withdrawn']
    blocked_scopes = {r.scope for r in open_withdrawals}
    complete_scopes = set.intersection(*scopes) - blocked_scopes
    return {
        'requirements': requirements,
        'evidence_complete': bool(complete_scopes),
        'complete_scopes': sorted(complete_scopes),
        'open_withdrawals': len(open_withdrawals),
        'blocked_scopes': sorted(blocked_scopes),
        'live_data_enabled': False,
        'notice': 'Evidence verification records an administrative review, not HIPAA certification or authorization to transfer data. Live intake and commercial release remain disabled.',
        'evidence': [{'id': r.id, 'category': r.category, 'reference': r.reference,
                      'sha256': r.sha256, 'scope': r.scope, 'status': r.status,
                      'review_history': r.review_history or [],
                      'expires_at': r.expires_at.isoformat() + 'Z',
                      'reviewed_at': r.reviewed_at.isoformat() + 'Z' if r.reviewed_at else None}
                     for r in rows],
    }
