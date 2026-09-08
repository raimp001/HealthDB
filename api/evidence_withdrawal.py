"""Administrative evidence withdrawal, not patient revocation or record deletion."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from .models import ResearchEvidence, Study, User, DataAccessLog


class Withdrawal(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    reference: str = Field(min_length=3, max_length=120, pattern=r'^[A-Za-z0-9_.:/-]+$')
    reason: str = Field(min_length=10, max_length=1000)


class Disposition(Withdrawal):
    future_use: Literal['stopped', 'not_applicable']
    recipients: Literal['notified', 'not_applicable']
    retained_data: Literal['removed', 'retained_under_reviewed_policy', 'not_applicable']


def register_evidence_withdrawal(app, get_db, require_user):
    def change(db, row, user, status, body):
        at = datetime.now(timezone.utc).isoformat()
        history = list(row.review_history or []) + [{
            'decision': status, 'reviewer_id': user.id, 'at': at, **body.model_dump()}]
        changed = db.query(ResearchEvidence).filter_by(id=row.id, status=row.status).update(
            {'status': status, 'review_history': history}, synchronize_session=False)
        if changed != 1:
            db.rollback()
            raise HTTPException(409, 'Evidence changed. Reload before retrying.')
        db.add(DataAccessLog(user_id=user.id, access_type='evidence_' + status,
                             data_type='research_evidence', purpose=row.study_id))
        db.commit()
        return {'status': status, 'live_data_enabled': False}

    @app.post('/api/research-evidence/{evidence_id}/withdraw')
    def withdraw(evidence_id: str, body: Withdrawal, user: User = Depends(require_user), db: Session = Depends(get_db)):
        row = db.query(ResearchEvidence).filter_by(id=evidence_id).with_for_update().first()
        if not row:
            raise HTTPException(404, 'Evidence not found')
        study = db.query(Study).filter_by(id=row.study_id).first()
        if user.user_type != 'admin' and study.user_id != user.id:
            raise HTTPException(403, 'Only the study owner or administrator can withdraw evidence')
        if row.status not in ('submitted', 'verified', 'revoked'):
            raise HTTPException(409, 'Evidence is already withdrawn or cannot be withdrawn')
        return change(db, row, user, 'withdrawn', body)

    @app.post('/api/research-evidence/{evidence_id}/disposition')
    def disposition(evidence_id: str, body: Disposition, user: User = Depends(require_user), db: Session = Depends(get_db)):
        if user.user_type != 'admin':
            raise HTTPException(403, 'An independent administrator must review the disposition')
        row = db.query(ResearchEvidence).filter_by(id=evidence_id).with_for_update().first()
        if not row:
            raise HTTPException(404, 'Evidence not found')
        if row.status != 'withdrawn':
            raise HTTPException(409, 'No open withdrawal for this evidence')
        withdrawal = (row.review_history or [])[-1]
        if user.id in (row.submitted_by, withdrawal.get('reviewer_id')):
            raise HTTPException(403, 'A different administrator must review the disposition')
        # Closing follow-up never verifies or reactivates the withdrawn evidence.
        return change(db, row, user, 'withdrawal_closed', body)
