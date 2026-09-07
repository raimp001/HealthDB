"""Tests for the continuous safety invariants.

Each invariant is tested twice: once on clean data, and once against the
exact violation it exists to catch. A check that only ever runs against a
healthy database has not been tested, because the failure mode that matters
is a check that is always green.
"""
import os
from datetime import datetime

import pytest

from api import self_audit
from api.self_audit import BLOCKER, Finding, run_audit


@pytest.fixture()
def db(client):
    """A session on the same disposable database the API is using."""
    session = client._session_factory()
    yield session
    session.close()


def make_owner(db, *, approved=True):
    """A study needs an owner; most of these tests do not care who."""
    from uuid import uuid4
    from api.models import User

    user = User(
        email=f"audit-owner-{uuid4()}@example.com", password_hash="x",
        name="Owner", user_type="researcher",
        researcher_approved_at=datetime.utcnow() if approved else None,
    )
    db.add(user)
    db.flush()
    return str(user.id)


# ---------------------------------------------------------------------------
# Report semantics
# ---------------------------------------------------------------------------

def test_warnings_do_not_gate_but_blockers_do():
    from api.self_audit import AuditReport, WARNING

    warning_only = AuditReport([Finding("w", False, WARNING, "")])
    assert warning_only.ok is True

    blocking = AuditReport([Finding("b", False, BLOCKER, "")])
    assert blocking.ok is False
    assert "b" in blocking.summary()


def test_a_check_that_raises_is_a_failure_not_a_pass(db):
    """The worst bug this module could have is going green on an exception."""
    def exploding(_db):
        raise RuntimeError("boom")

    report = run_audit(db, checks=[exploding])
    assert report.ok is False
    assert report.findings[0].severity == BLOCKER
    assert "could not run" in report.findings[0].summary
    # The exception message must not be echoed; it can carry query fragments.
    assert "boom" not in report.findings[0].summary


def test_one_failing_check_does_not_abort_the_others(db):
    def exploding(_db):
        raise RuntimeError("boom")

    report = run_audit(db, checks=[exploding, self_audit.check_pilot_flags])
    assert len(report.findings) == 2


def test_findings_are_json_serializable(db):
    import json
    json.dumps(run_audit(db).as_dict())


# ---------------------------------------------------------------------------
# Individual invariants: clean, then violated
# ---------------------------------------------------------------------------

def test_a_stored_placeholder_is_reported_but_not_served(db):
    """Filtering removes the harm; the row still owes a cleanup.

    The two checks must move independently. If the stored row could make the
    served check fail, or the filter could make the stored check pass, one
    would hide the other.
    """
    from api.main import PLACEHOLDER_INSTITUTION_NAMES
    from api.models import Institution

    assert self_audit.check_no_placeholder_institutions_served(db).passed is True
    assert self_audit.check_no_placeholder_institutions_stored(db).passed is True

    name = sorted(PLACEHOLDER_INSTITUTION_NAMES)[0]
    db.add(Institution(name=name, is_active=True))
    db.commit()

    served = self_audit.check_no_placeholder_institutions_served(db)
    assert served.passed is True, "a stored row that is filtered out is not served"

    stored = self_audit.check_no_placeholder_institutions_stored(db)
    assert stored.passed is False
    assert stored.severity == self_audit.WARNING, "filtered out, so not a blocker"
    assert stored.count == 1
    assert name in stored.detail["names"]
    assert "manage remove-placeholder-institutions" in stored.summary


def test_a_seeded_name_that_reached_a_caller_is_a_blocker(db, monkeypatch):
    """If the filter is ever removed, the audit must go red immediately."""
    import api.main as main
    from api.models import Institution

    name = sorted(main.PLACEHOLDER_INSTITUTION_NAMES)[0]
    db.add(Institution(name=name, is_active=True))
    db.commit()

    # Simulate the filter being dropped from the serving query.
    monkeypatch.setattr(
        main, "servable_institutions",
        lambda session: session.query(Institution).filter(Institution.is_active == True),
    )
    finding = self_audit.check_no_placeholder_institutions_served(db)
    assert finding.passed is False
    assert finding.severity == self_audit.BLOCKER
    assert name in finding.detail["names"]


def test_a_completed_export_without_a_risk_report_is_caught(db):
    from api.models import ExtractionJob, Study

    assert self_audit.check_completed_exports_were_risk_assessed(db).passed is True

    study = Study(name="S", user_id=make_owner(db))
    db.add(study); db.flush()
    db.add(ExtractionJob(study_id=study.id, status="completed", disclosure_risk=None))
    db.commit()

    finding = self_audit.check_completed_exports_were_risk_assessed(db)
    assert finding.passed is False
    assert finding.detail["unassessed"] == 1


def test_a_completed_export_released_below_threshold_is_caught(db):
    from api.models import ExtractionJob, Study

    study = Study(name="S", user_id=make_owner(db))
    db.add(study); db.flush()
    db.add(ExtractionJob(study_id=study.id, status="completed",
                         disclosure_risk={"min_k": 1, "meets_threshold": False}))
    db.commit()

    finding = self_audit.check_completed_exports_were_risk_assessed(db)
    assert finding.passed is False
    assert finding.detail["below_threshold"] == 1


def test_a_tampered_manifest_is_caught(db):
    from api.models import DataRelease, Study
    from api.release_manifest import build_manifest, manifest_digest

    study = Study(name="S", user_id=make_owner(db))
    db.add(study); db.flush()
    manifest = build_manifest(
        job_id="j", study_id=str(study.id), study_name="S", released_to="u",
        released_at="2026-01-01T00:00:00", variables=["a"], subject_count=11,
        record_count=11, content_digest="abc", cohort_criteria=None,
        disclosure_risk={"meets_threshold": True},
        approvals=[{"id": "1", "document_type": "irb_protocol", "status": "approved"},
                   {"id": "2", "document_type": "dua", "status": "signed"}],
        deidentification_level="limited_dataset",
    )
    release = DataRelease(
        job_id="j", study_id=str(study.id), manifest=manifest,
        manifest_digest=manifest_digest(manifest), content_digest="abc",
        subject_count=11, record_count=11, subject_ids=[],
    )
    db.add(release); db.commit()
    assert self_audit.check_release_manifests_verify(db).passed is True

    # Rewrite history: claim more subjects than were actually released.
    tampered = dict(manifest, subject_count=99)
    release.manifest = tampered
    db.commit()

    finding = self_audit.check_release_manifests_verify(db)
    assert finding.passed is False
    assert str(release.id) in finding.detail["release_ids"]


def test_a_release_without_irb_and_dua_is_caught(db):
    from api.models import DataRelease, Study
    from api.release_manifest import build_manifest, manifest_digest

    study = Study(name="S", user_id=make_owner(db))
    db.add(study); db.flush()
    manifest = build_manifest(
        job_id="j", study_id=str(study.id), study_name="S", released_to="u",
        released_at="2026-01-01T00:00:00", variables=["a"], subject_count=11,
        record_count=11, content_digest="abc", cohort_criteria=None,
        disclosure_risk=None,
        approvals=[{"id": "1", "document_type": "irb_protocol", "status": "approved"}],
        deidentification_level="limited_dataset",
    )
    db.add(DataRelease(
        job_id="j", study_id=str(study.id), manifest=manifest,
        manifest_digest=manifest_digest(manifest), content_digest="abc",
        subject_count=11, record_count=11, subject_ids=[],
    ))
    db.commit()

    finding = self_audit.check_releases_had_approvals(db)
    assert finding.passed is False, "a release with no signed DUA must be caught"


def test_an_untracked_revocation_is_caught(db):
    """A patient revoked, and a release carrying them was never flagged."""
    from api.models import Consent, DataRelease, PatientProfile, Study

    study = Study(name="S", user_id=make_owner(db))
    patient = PatientProfile()
    db.add_all([study, patient]); db.flush()
    db.add_all([
        Consent(patient_id=patient.id, consent_type="research_data_sharing",
                status="revoked", revoked_at=datetime.utcnow()),
        DataRelease(job_id="j", study_id=str(study.id), manifest={},
                    manifest_digest="x", content_digest="y",
                    subject_count=1, record_count=1,
                    subject_ids=[str(patient.id)]),
    ])
    db.commit()

    finding = self_audit.check_revocations_are_tracked(db)
    assert finding.passed is False
    assert finding.count == 1


def test_a_tracked_revocation_passes(db):
    from api.models import Consent, DataRelease, PatientProfile, Study

    study = Study(name="S", user_id=make_owner(db))
    patient = PatientProfile()
    db.add_all([study, patient]); db.flush()
    db.add_all([
        Consent(patient_id=patient.id, consent_type="research_data_sharing",
                status="revoked", revoked_at=datetime.utcnow()),
        DataRelease(job_id="j", study_id=str(study.id), manifest={},
                    manifest_digest="x", content_digest="y",
                    subject_count=1, record_count=1,
                    subject_ids=[str(patient.id)],
                    withdrawal_required_at=datetime.utcnow()),
    ])
    db.commit()

    assert self_audit.check_revocations_are_tracked(db).passed is True


def test_an_unapproved_study_owner_is_caught(db, client, register):
    from api.models import Study, User

    body = register("audit-unapproved@example.com").json()
    user_id = body["user"]["id"]
    db.add(Study(name="S", user_id=user_id))
    db.commit()

    finding = self_audit.check_no_unapproved_researcher_holds_studies(db)
    assert finding.passed is False
    assert finding.count == 1

    db.query(User).filter(User.id == user_id).update(
        {"researcher_approved_at": datetime.utcnow()})
    db.commit()
    assert self_audit.check_no_unapproved_researcher_holds_studies(db).passed is True


def test_a_lowered_export_threshold_is_caught(db, monkeypatch):
    import api.main as main

    assert self_audit.check_export_threshold_not_lowered(db).passed is True

    monkeypatch.setattr(main, "MIN_EXPORT_K", 2)
    finding = self_audit.check_export_threshold_not_lowered(db)
    assert finding.passed is False
    assert "lowered to 2" in finding.summary


def test_a_weak_jwt_secret_is_caught(db, monkeypatch):
    assert self_audit.check_secrets_configured(db).passed is True

    monkeypatch.setenv("JWT_SECRET", "hunter2")
    finding = self_audit.check_secrets_configured(db)
    assert finding.passed is False
    # The verdict may say whether one is configured, never what it is.
    assert "hunter2" not in finding.summary
    assert "hunter2" not in str(finding.detail)
    assert finding.detail == {"configured": True}


def test_pilot_flags_are_reported_without_gating(db, monkeypatch):
    monkeypatch.setenv("ENABLE_DATA_MARKETPLACE", "true")
    finding = self_audit.check_pilot_flags(db)
    assert finding.passed is True, "reporting posture must not fail the audit"
    assert "ENABLE_DATA_MARKETPLACE" in finding.detail["enabled"]


def test_no_finding_leaks_a_patient_identifier(db, client, register):
    """Findings carry counts and labels. Never a subject id."""
    from api.models import Consent, DataRelease, PatientProfile, Study

    study = Study(name="S", user_id=make_owner(db))
    patient = PatientProfile()
    db.add_all([study, patient]); db.flush()
    patient_id = str(patient.id)
    db.add_all([
        Consent(patient_id=patient.id, consent_type="research_data_sharing",
                status="revoked", revoked_at=datetime.utcnow()),
        DataRelease(job_id="j", study_id=str(study.id), manifest={},
                    manifest_digest="x", content_digest="y",
                    subject_count=1, record_count=1, subject_ids=[patient_id]),
    ])
    db.commit()

    import json
    serialized = json.dumps(run_audit(db).as_dict())
    assert patient_id not in serialized
