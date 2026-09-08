"""Self-declared site feasibility. No patient values or availability counts."""
from datetime import datetime
from typing import Literal
from fastapi import Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import ResearchPlan, SiteFeasibility, User, DataAccessLog


class Mapping(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    variable: str = Field(min_length=1, max_length=80)
    availability: Literal['unknown', 'available', 'derivable', 'unavailable'] = 'unknown'
    source: str = Field(default='', max_length=200)
    transformation: str = Field(default='', max_length=500)


class Declaration(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    revision: int = Field(ge=0)
    plan_revision: int = Field(ge=1)
    site_label: str = Field(min_length=3, max_length=150)
    approvals_needed: str = Field(default='', max_length=1000)
    mappings: list[Mapping] = Field(max_length=100)

    @model_validator(mode='after')
    def valid_mappings(self):
        names = [m.variable for m in self.mappings]
        if len(names) != len(set(names)):
            raise ValueError('Each variable needs exactly one mapping')
        for m in self.mappings:
            if m.availability in ('available', 'derivable') and not m.source:
                raise ValueError('Available or derivable variables need an expected source')
            if m.availability == 'derivable' and not m.transformation:
                raise ValueError('Derivable variables need a transformation description')
        return self


def register_site_feasibility(app, get_db, require_user, require_access):
    @app.get('/api/workspace/projects/{study_id}/feasibility')
    def read(study_id: str, response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
        require_access(db, study_id, user.id)
        plan = db.get(ResearchPlan, study_id)
        response.headers['Cache-Control'] = 'no-store'
        rows = db.query(SiteFeasibility, User.name).join(User, User.id == SiteFeasibility.user_id).filter(SiteFeasibility.study_id == study_id).order_by(SiteFeasibility.updated_at.desc()).limit(200).all()
        return {'plan_revision': plan.revision if plan else 0,
                'variables': plan.content.get('variables', []) if plan else [],
                'declarations': [{**r.content, 'revision': r.revision, 'plan_revision': r.plan_revision,
                                  'reporter': name, 'mine': r.user_id == user.id,
                                  'stale': not plan or r.plan_revision != plan.revision} for r, name in rows]}

    @app.put('/api/workspace/projects/{study_id}/feasibility')
    def save(study_id: str, body: Declaration, user: User = Depends(require_user), db: Session = Depends(get_db)):
        require_access(db, study_id, user.id)
        plan = db.query(ResearchPlan).filter_by(study_id=study_id).with_for_update().first()
        if not plan or plan.revision != body.plan_revision:
            raise HTTPException(409, 'The study plan changed. Reload and reconcile your mappings.')
        expected = {v['name'] for v in plan.content.get('variables', [])}
        if not expected or {m.variable for m in body.mappings} != expected:
            raise HTTPException(422, 'Map every variable in the saved study specification, with no additional variables.')
        content = body.model_dump(exclude={'revision', 'plan_revision'})
        try:
            if body.revision == 0:
                db.add(SiteFeasibility(study_id=study_id, user_id=user.id, revision=1,
                                       plan_revision=body.plan_revision, content=content))
                db.flush()
            else:
                changed = db.query(SiteFeasibility).filter_by(study_id=study_id, user_id=user.id, revision=body.revision).update({
                    'revision': body.revision + 1, 'plan_revision': body.plan_revision,
                    'content': content, 'updated_at': datetime.utcnow()})
                if changed != 1:
                    raise HTTPException(409, 'Your declaration changed in another session. Reload before saving.')
            db.add(DataAccessLog(user_id=user.id, access_type='site_feasibility_saved', data_type='research_plan', purpose=study_id))
            db.commit()
        except IntegrityError:
            db.rollback(); raise HTTPException(409, 'A declaration already exists. Reload before saving.')
        return {'revision': body.revision + 1}
