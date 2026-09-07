"""Research planning and opt-in discovery. Planning never grants data access."""
from datetime import datetime
from typing import Literal
from fastapi import Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import Study, User, ResearchPlan, ResearchInterest, StudyCollaborator, StudyComment, DataAccessLog


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Variable(StrictModel):
    name: str = Field(min_length=1, max_length=80, pattern=r'^[a-z][a-z0-9_]*$')
    definition: str = Field(min_length=3, max_length=500)
    type: Literal['number', 'category', 'boolean', 'year'] = 'category'
    source: str = Field(default='', max_length=150)
    units: str = Field(default='', max_length=80)
    required: bool = True


class Milestone(StrictModel):
    title: str = Field(min_length=3, max_length=150)
    owner: str = Field(default='', max_length=100)
    status: Literal['todo', 'in_progress', 'done'] = 'todo'


class Plan(StrictModel):
    question: str = Field(default='', max_length=1000)
    population: str = Field(default='', max_length=1000)
    exposure: str = Field(default='', max_length=1000)
    outcome: str = Field(default='', max_length=1000)
    analysis: str = Field(default='', max_length=2000)
    impact: str = Field(default='', max_length=1000)
    seeking: str = Field(default='', max_length=300)
    variables: list[Variable] = Field(default_factory=list, max_length=100)
    milestones: list[Milestone] = Field(default_factory=list, max_length=40)

    @model_validator(mode='after')
    def unique_names(self):
        names = [v.name for v in self.variables]
        if len(set(names)) != len(names):
            raise ValueError('Variable names must be unique')
        return self


class SavePlan(StrictModel):
    revision: int = Field(ge=0)
    listed: bool = False
    plan: Plan


class NewStudy(StrictModel):
    name: str = Field(min_length=3, max_length=150)


class Interest(StrictModel):
    message: str = Field(min_length=10, max_length=1000)


class ReviewInterest(StrictModel):
    decision: Literal['invite', 'decline']


def register_workspace(app, get_db, require_user, require_access):
    def audit(db, user, action, study_id):
        db.add(DataAccessLog(user_id=user.id, access_type=action, data_type='research_plan', purpose=study_id))

    @app.get('/api/workspace/projects')
    def projects(response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        response.headers['Cache-Control'] = 'no-store'
        shared = db.query(StudyCollaborator.study_id).filter(StudyCollaborator.user_id == user.id, StudyCollaborator.status == 'accepted')
        rows = db.query(Study).filter(or_(Study.user_id == user.id, Study.id.in_(shared))).order_by(Study.created_at.desc()).limit(200).all()
        return [{'id': s.id, 'name': s.name, 'owner': s.user_id == user.id} for s in rows]

    @app.post('/api/workspace/projects', status_code=201)
    def create(body: NewStudy, user: User = Depends(require_user), db: Session = Depends(get_db)):
        s = Study(name=body.name, user_id=user.id, principal_investigator=user.name, status='draft')
        db.add(s); db.flush(); audit(db, user, 'plan_created', s.id); db.commit()
        return {'id': s.id, 'name': s.name}

    @app.get('/api/workspace/projects/{study_id}')
    def get_plan(study_id: str, response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        s = require_access(db, study_id, user.id)
        row = db.get(ResearchPlan, study_id)
        response.headers['Cache-Control'] = 'no-store'
        return {'id': s.id, 'name': s.name, 'can_edit': s.user_id == user.id,
                'revision': row.revision if row else 0, 'listed': bool(row and row.listed),
                'plan': row.content if row else Plan().model_dump()}

    @app.put('/api/workspace/projects/{study_id}')
    def save(study_id: str, body: SavePlan, user: User = Depends(require_user), db: Session = Depends(get_db)):
        s = require_access(db, study_id, user.id)
        if s.user_id != user.id:
            raise HTTPException(403, 'Only the study owner can edit the plan. Share suggestions in the study discussion.')
        if body.listed and not all([body.plan.question, body.plan.population, body.plan.outcome, body.plan.seeking]):
            raise HTTPException(422, 'Add a question, population, outcome and collaborator needs before listing.')
        try:
            if body.revision == 0:
                db.add(ResearchPlan(study_id=study_id, revision=1, content=body.plan.model_dump(), listed=body.listed))
                db.flush()
            else:
                changed = db.query(ResearchPlan).filter(ResearchPlan.study_id == study_id, ResearchPlan.revision == body.revision).update({
                    'revision': body.revision + 1, 'content': body.plan.model_dump(), 'listed': body.listed, 'updated_at': datetime.utcnow()})
                if changed != 1:
                    raise HTTPException(409, 'The plan changed. Reload it before saving; your edits have not overwritten it.')
            audit(db, user, 'plan_saved', study_id); db.commit()
        except IntegrityError:
            db.rollback(); raise HTTPException(409, 'The plan changed. Reload before saving.')
        return {'revision': body.revision + 1}

    @app.get('/api/workspace/opportunities')
    def opportunities(response: Response, q: str = Query('', max_length=100), offset: int = Query(0, ge=0), user: User = Depends(require_user), db: Session = Depends(get_db)):
        response.headers['Cache-Control'] = 'no-store'
        query = db.query(Study, ResearchPlan).join(ResearchPlan, Study.id == ResearchPlan.study_id).join(User, User.id == Study.user_id).filter(ResearchPlan.listed.is_(True), User.is_active.is_(True), or_(User.user_type == 'admin', (User.user_type == 'researcher') & User.is_verified.is_(True) & User.researcher_approved_at.isnot(None)))
        if q:
            query = query.filter(Study.name.ilike('%' + q.replace('%', '\\%').replace('_', '\\_') + '%', escape='\\'))
        rows = query.order_by(ResearchPlan.updated_at.desc(), Study.id).offset(offset).limit(21).all()
        return {'has_more': len(rows) > 20, 'items': [{'id': s.id, 'name': s.name, 'question': p.content.get('question', ''), 'seeking': p.content.get('seeking', ''), 'mine': s.user_id == user.id} for s, p in rows[:20]]}

    @app.get('/api/workspace/projects/{study_id}/discussion')
    def discussion(study_id: str, response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        require_access(db, study_id, user.id)
        response.headers['Cache-Control'] = 'no-store'
        rows = db.query(StudyComment, User.name).join(User, User.id == StudyComment.user_id).filter(StudyComment.study_id == study_id).order_by(StudyComment.created_at.desc()).limit(100).all()
        return [{'id': c.id, 'name': name, 'message': c.content} for c, name in rows]

    @app.post('/api/workspace/projects/{study_id}/discussion', status_code=201)
    def comment(study_id: str, body: Interest, user: User = Depends(require_user), db: Session = Depends(get_db)):
        require_access(db, study_id, user.id)
        db.add(StudyComment(study_id=study_id, user_id=user.id, content=body.message))
        db.commit()
        return {'status': 'posted'}

    @app.post('/api/workspace/opportunities/{study_id}/interest', status_code=201)
    def express_interest(study_id: str, body: Interest, user: User = Depends(require_user), db: Session = Depends(get_db)):
        if user.user_type != 'researcher':
            raise HTTPException(403, 'Collaboration requests require an approved researcher account')
        plan = db.get(ResearchPlan, study_id); study = db.get(Study, study_id)
        if not plan or not plan.listed or not study:
            raise HTTPException(404, 'Project is not listed')
        if study.user_id == user.id:
            raise HTTPException(409, 'You own this project')
        if db.query(StudyCollaborator).filter_by(study_id=study_id, user_id=user.id, status='accepted').first():
            raise HTTPException(409, 'You already belong to this team')
        db.add(ResearchInterest(study_id=study_id, user_id=user.id, message=body.message))
        try:
            db.commit()
        except IntegrityError:
            db.rollback(); raise HTTPException(409, 'Your interest has already been recorded')
        return {'status': 'pending', 'message': 'Request recorded in the owner inbox. No email was sent or access granted.'}

    @app.get('/api/workspace/projects/{study_id}/interests')
    def interests(study_id: str, response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        s = require_access(db, study_id, user.id)
        if s.user_id != user.id:
            raise HTTPException(403, 'Only the owner can review requests')
        response.headers['Cache-Control'] = 'no-store'
        rows = db.query(ResearchInterest, User).join(User, User.id == ResearchInterest.user_id).filter(ResearchInterest.study_id == study_id).order_by(ResearchInterest.created_at.desc()).limit(200).all()
        return [{'id': r.id, 'name': u.name, 'organization': u.organization, 'message': r.message, 'status': r.status} for r,u in rows]

    @app.post('/api/workspace/projects/{study_id}/interests/{interest_id}')
    def review(study_id: str, interest_id: str, body: ReviewInterest, user: User = Depends(require_user), db: Session = Depends(get_db)):
        s = require_access(db, study_id, user.id)
        if s.user_id != user.id:
            raise HTTPException(403, 'Only the owner can review requests')
        row = db.query(ResearchInterest).filter_by(id=interest_id, study_id=study_id).with_for_update().first()
        if not row:
            raise HTTPException(404, 'Request not found')
        if row.status != 'pending':
            raise HTTPException(409, 'This request was already reviewed')
        if body.decision == 'invite':
            target = db.get(User, row.user_id)
            if not target or not target.is_active or not target.is_verified or target.user_type != 'researcher' or not target.researcher_approved_at:
                raise HTTPException(409, 'Applicant needs active, verified, approved researcher access')
            existing = db.query(StudyCollaborator).filter(StudyCollaborator.study_id == study_id, or_(StudyCollaborator.user_id == row.user_id, StudyCollaborator.email == target.email)).first()
            if existing:
                raise HTTPException(409, 'An invitation or membership already exists. Review it in the collaboration workspace.')
            db.add(StudyCollaborator(study_id=study_id, user_id=target.id, email=target.email, role='co_investigator', status='invited', permissions={}))
        row.status = 'invited' if body.decision == 'invite' else 'declined'
        audit(db, user, 'interest_' + row.status, study_id); db.commit()
        return {'status': row.status}
