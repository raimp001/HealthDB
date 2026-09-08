"""Research work credit with application-level append-only review events; no payouts."""
from fastapi import Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from sqlalchemy.orm import Session
from .models import User, WorkContribution, WorkContributionEvent, DataAccessLog


class Submission(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=1000)
    evidence_ref: str = Field(min_length=3, max_length=300)
    minutes: int = Field(ge=1, le=100000)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    revision: int = Field(ge=1)
    action: Literal['accepted', 'changes_requested', 'disputed', 'resubmitted']
    reason: str = Field(min_length=10, max_length=1000)
    policy_ref: str = Field(default='', max_length=300)


def register_work_ledger(app, get_db, require_user, require_access):
    def event(db, row, user, action, content):
        db.add(WorkContributionEvent(contribution_id=row.id, revision=row.revision,
            actor_id=user.id, action=action, content=content))
        db.add(DataAccessLog(user_id=user.id, access_type='work_contribution_' + action,
                             data_type='research_work', purpose=row.study_id))

    @app.get('/api/workspace/projects/{study_id}/contributions')
    def read(study_id: str, response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        study = require_access(db, study_id, user.id)
        response.headers['Cache-Control'] = 'no-store'
        rows = db.query(WorkContribution).filter_by(study_id=study_id).order_by(WorkContribution.id).limit(201).all()
        rows_page = rows[:200]
        ids = [r.id for r in rows_page]
        events = db.query(WorkContributionEvent, User.name).join(User, User.id == WorkContributionEvent.actor_id).filter(
            WorkContributionEvent.contribution_id.in_(ids)).order_by(WorkContributionEvent.revision).all() if ids else []
        history = {}
        for e, name in events:
            history.setdefault(e.contribution_id, []).append({'revision': e.revision, 'actor': name,
                'action': e.action, 'content': e.content, 'timestamp': e.created_at.isoformat() + 'Z'})
        return {'has_more': len(rows) > 200, 'items': [{**r.content, 'id': r.id, 'revision': r.revision,
            'status': r.status, 'mine': r.user_id == user.id,
            'can_review': study.user_id == user.id and r.user_id != user.id,
            'events': history.get(r.id, [])} for r in rows_page]}

    @app.post('/api/workspace/projects/{study_id}/contributions', status_code=201)
    def submit(study_id: str, body: Submission, user: User = Depends(require_user), db: Session = Depends(get_db)):
        require_access(db, study_id, user.id)
        row = WorkContribution(study_id=study_id, user_id=user.id, content=body.model_dump())
        db.add(row); db.flush()
        event(db, row, user, 'submitted', body.model_dump())
        db.commit()
        return {'id': row.id, 'revision': row.revision}

    @app.post('/api/workspace/projects/{study_id}/contributions/{contribution_id}/events')
    def review(study_id: str, contribution_id: str, body: Decision, user: User = Depends(require_user), db: Session = Depends(get_db)):
        study = require_access(db, study_id, user.id)
        row = db.query(WorkContribution).filter_by(id=contribution_id, study_id=study_id).with_for_update().first()
        if not row:
            raise HTTPException(404, 'Contribution not found')
        is_review = body.action in ('accepted', 'changes_requested')
        if is_review and (study.user_id != user.id or row.user_id == user.id):
            raise HTTPException(403, 'Only the project owner can review another member’s work. No self-approval.')
        if not is_review and row.user_id != user.id:
            raise HTTPException(403, 'Only the contributor can dispute or resubmit this work')
        if body.revision != row.revision:
            raise HTTPException(409, 'This contribution changed. Reload before acting.')
        allowed = {'accepted': {'submitted', 'resubmitted', 'disputed'},
                   'changes_requested': {'submitted', 'resubmitted', 'disputed'},
                   'disputed': {'accepted', 'changes_requested'},
                   'resubmitted': {'changes_requested'}}
        if row.status not in allowed[body.action]:
            raise HTTPException(409, 'This action is not available for the current status')
        if not is_review and body.policy_ref:
            raise HTTPException(422, 'Policy references belong to review decisions')
        # Conditional update also protects environments without row-level locks.
        changed = db.query(WorkContribution).filter_by(id=row.id, revision=body.revision).update(
            {'revision': body.revision + 1, 'status': body.action}, synchronize_session=False)
        if changed != 1:
            raise HTTPException(409, 'This contribution changed. Reload before acting.')
        db.refresh(row)
        event(db, row, user, body.action, body.model_dump(exclude={'revision', 'action'}))
        db.commit()
        return {'revision': row.revision, 'status': row.status}
