"""Continuous checks that the platform's safety properties still hold.

Tests prove the code was correct when it was written. They say nothing about
the database three months later, after a migration that was never run, a
seeder that was re-run by accident, or an environment variable somebody
lowered to get an export through.

Every invariant here is a property that was, at some point, asserted to be
true in a document or on the website. This module re-derives each one from
live data, so a claim that has quietly stopped being true becomes a visible
failure rather than a surprise during an audit.

Design rules, which matter more than the checks themselves:

* **No PHI leaves this module.** Findings carry counts and non-identifying
  labels. A finding that named the affected patients would be a new
  disclosure created by the privacy checker.
* **Every check is read-only.** Nothing here repairs anything. A checker that
  silently fixes what it finds destroys the evidence that it was ever broken.
* **A check that cannot run is a failure, not a pass.** An exception is
  reported as `error`, never swallowed into `ok`. The most dangerous possible
  bug in this file is one that makes it always green.
"""
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List

from sqlalchemy import text
from sqlalchemy.orm import Session

# Severity drives what an operator does, not how alarming it sounds.
BLOCKER = "blocker"      # a safety property is currently violated
WARNING = "warning"      # not violated, but heading that way or unverifiable
INFO = "info"            # posture worth reporting, no action implied


@dataclass
class Finding:
    name: str
    passed: bool
    severity: str
    summary: str
    count: int = 0
    detail: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name, "passed": self.passed, "severity": self.severity,
            "summary": self.summary, "count": self.count, "detail": self.detail,
        }


@dataclass
class AuditReport:
    findings: List[Finding]

    @property
    def blockers(self) -> List[Finding]:
        return [f for f in self.findings if not f.passed and f.severity == BLOCKER]

    @property
    def ok(self) -> bool:
        """False if any blocker is failing. Warnings do not gate."""
        return not self.blockers

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "blocker_count": len(self.blockers),
            "checked": len(self.findings),
            "findings": [f.as_dict() for f in self.findings],
        }

    def summary(self) -> str:
        if self.ok:
            failing = [f for f in self.findings if not f.passed]
            suffix = f" ({len(failing)} warning(s))" if failing else ""
            return f"All {len(self.findings)} invariants hold{suffix}."
        names = ", ".join(f.name for f in self.blockers)
        return f"{len(self.blockers)} blocker(s) failing: {names}"


# --------------------------------------------------------------------------
# Invariants. Each takes a Session and returns a Finding.
# --------------------------------------------------------------------------

def check_no_precise_clinical_dates(db: Session) -> Finding:
    """Safe Harbor forbids dates more precise than year.

    The schema moved to `original_year`, but the old `original_date` column
    survives until `manage.py migrate-dates` is run, and until then it still
    holds month and day.
    """
    # Probe the table first. Without this, a database outage would make the
    # column query fail and be read as "the column is gone" — the exact
    # green-because-it-crashed result this module is supposed to prevent.
    db.execute(text("SELECT COUNT(*) FROM extracted_medical_data")).scalar()
    try:
        remaining = db.execute(text(
            "SELECT COUNT(*) FROM extracted_medical_data WHERE original_date IS NOT NULL"
        )).scalar() or 0
    except Exception:
        # The table is reachable but the column is not: it has been dropped,
        # which is the desired end state.
        db.rollback()
        return Finding(
            "no_precise_clinical_dates", True, BLOCKER,
            "original_date column is absent; no month/day precision is stored.",
        )
    return Finding(
        "no_precise_clinical_dates", remaining == 0, BLOCKER,
        "No stored clinical date is more precise than a year."
        if remaining == 0 else
        f"{remaining} record(s) still hold month/day precision. "
        "Run: python -m api.manage migrate-dates",
        count=remaining,
    )


def check_no_placeholder_institutions(db: Session) -> Finding:
    """Seeded rows naming real hospitals were served as though they were partners."""
    from .models import Institution
    from .main import PLACEHOLDER_INSTITUTION_NAMES

    names = [
        row.name for row in db.query(Institution).filter(
            Institution.name.in_(PLACEHOLDER_INSTITUTION_NAMES)
        ).all()
    ]
    return Finding(
        "no_placeholder_institutions", not names, BLOCKER,
        "No seeded organisation names are being served as partners."
        if not names else
        f"{len(names)} real organisation name(s) served with no relationship. "
        "Run: python -m api.manage remove-placeholder-institutions",
        count=len(names),
        # Organisation names are not PHI, and an operator needs to know which.
        detail={"names": sorted(names)},
    )


def check_completed_exports_were_risk_assessed(db: Session) -> Finding:
    """Every released extract must carry a passing disclosure-risk report.

    A completed job with no report predates the gate, or got around it.
    Either way it was released without the measurement.
    """
    from .models import ExtractionJob

    jobs = db.query(ExtractionJob).filter(ExtractionJob.status == "completed").all()
    unassessed = [j for j in jobs if not j.disclosure_risk]
    failing = [
        j for j in jobs
        if j.disclosure_risk and not j.disclosure_risk.get("meets_threshold")
    ]
    bad = len(unassessed) + len(failing)
    return Finding(
        "completed_exports_were_risk_assessed", bad == 0, BLOCKER,
        f"All {len(jobs)} completed export(s) carry a passing risk report."
        if bad == 0 else
        f"{len(unassessed)} completed export(s) have no risk report and "
        f"{len(failing)} were released below threshold.",
        count=bad,
        detail={"unassessed": len(unassessed), "below_threshold": len(failing)},
    )


def check_completed_exports_have_manifests(db: Session) -> Finding:
    """A release with no manifest cannot be reproduced, cited or withdrawn."""
    from .models import DataRelease, ExtractionJob

    completed = {
        str(j.id) for j in
        db.query(ExtractionJob).filter(ExtractionJob.status == "completed").all()
    }
    with_manifest = {str(r.job_id) for r in db.query(DataRelease).all()}
    missing = completed - with_manifest
    return Finding(
        "completed_exports_have_manifests", not missing, WARNING,
        f"All {len(completed)} completed export(s) have a release manifest."
        if not missing else
        f"{len(missing)} completed export(s) predate or bypassed manifesting; "
        "their contents cannot be reconstructed.",
        count=len(missing),
    )


def check_release_manifests_verify(db: Session) -> Finding:
    """A manifest that no longer hashes to its recorded digest is not evidence."""
    from .models import DataRelease
    from .release_manifest import verify_manifest

    releases = db.query(DataRelease).all()
    tampered = [
        str(r.id) for r in releases
        if not verify_manifest(r.manifest or {}, r.manifest_digest or "")
    ]
    return Finding(
        "release_manifests_verify", not tampered, BLOCKER,
        f"All {len(releases)} release manifest(s) match their recorded digest."
        if not tampered else
        f"{len(tampered)} manifest(s) no longer match their digest. "
        "They cannot be cited as a record of what was supplied.",
        count=len(tampered),
        detail={"release_ids": sorted(tampered)},
    )


def check_releases_had_approvals(db: Session) -> Finding:
    """Every release must record an IRB approval and a signed DUA in force."""
    from .models import DataRelease

    unapproved = []
    for release in db.query(DataRelease).all():
        approvals = (release.manifest or {}).get("approvals") or []
        types = {
            a.get("document_type") for a in approvals
            if a.get("status") in {"approved", "signed"}
        }
        if not {"irb_protocol", "dua"}.issubset(types):
            unapproved.append(str(release.id))
    return Finding(
        "releases_had_approvals", not unapproved, BLOCKER,
        "Every release recorded an IRB approval and a signed DUA."
        if not unapproved else
        f"{len(unapproved)} release(s) record no IRB approval and signed DUA.",
        count=len(unapproved),
        detail={"release_ids": sorted(unapproved)},
    )


def check_revocations_are_tracked(db: Session) -> Finding:
    """A revoking patient's prior releases must be flagged for follow-up.

    Revocation stops future extracts. It does not reach a file a researcher
    already holds, so the obligation has to be recorded against the release
    or it does not exist.
    """
    from .models import Consent, DataRelease

    revoked_patients = {
        str(pid) for (pid,) in db.query(Consent.patient_id).filter(
            Consent.status == "revoked"
        ).all()
    }
    if not revoked_patients:
        return Finding(
            "revocations_are_tracked", True, BLOCKER,
            "No revoked consents; nothing to track.",
        )

    untracked = [
        str(release.id) for release in db.query(DataRelease).all()
        if release.withdrawal_required_at is None
        and revoked_patients & {str(s) for s in (release.subject_ids or [])}
    ]
    return Finding(
        "revocations_are_tracked", not untracked, BLOCKER,
        f"All releases touching {len(revoked_patients)} revoking patient(s) are flagged."
        if not untracked else
        f"{len(untracked)} release(s) contain a patient who has revoked but "
        "carry no withdrawal obligation.",
        count=len(untracked),
        detail={"release_ids": sorted(untracked)},
    )


def check_no_unapproved_researcher_holds_studies(db: Session) -> Finding:
    """Approval is what authorizes research access; a study without it is a gap."""
    from .models import Study, User

    owners = {str(s.user_id) for s in db.query(Study).all() if s.user_id}
    if not owners:
        return Finding(
            "no_unapproved_researcher_holds_studies", True, BLOCKER,
            "No studies exist.",
        )
    unapproved = db.query(User).filter(
        User.id.in_(owners),
        User.researcher_approved_at == None,
        User.user_type != "admin",
    ).count()
    return Finding(
        "no_unapproved_researcher_holds_studies", unapproved == 0, BLOCKER,
        f"All {len(owners)} study owner(s) are approved researchers."
        if unapproved == 0 else
        f"{unapproved} study owner(s) have never been approved. "
        "Run: python -m api.manage approve-researcher, or remove the study.",
        count=unapproved,
    )


def check_export_threshold_not_lowered(db: Session) -> Finding:
    """A deployer can lower MIN_EXPORT_K by environment variable.

    That is deliberate — a pilot with tiny synthetic cohorts needs it — but an
    override must never be invisible, because the whole disclosure gate rests
    on this number.
    """
    from .main import MIN_AGGREGATE_CELL_SIZE, MIN_EXPORT_K

    floor = 11
    overridden = "MIN_EXPORT_K" in os.environ
    return Finding(
        "export_threshold_not_lowered", MIN_EXPORT_K >= floor, BLOCKER,
        f"Export k threshold is {MIN_EXPORT_K} (floor {floor})."
        if MIN_EXPORT_K >= floor else
        f"Export k threshold has been lowered to {MIN_EXPORT_K}, below the "
        f"floor of {floor}. Extracts are being released at higher risk.",
        count=MIN_EXPORT_K,
        detail={
            "min_export_k": MIN_EXPORT_K,
            "min_aggregate_cell_size": MIN_AGGREGATE_CELL_SIZE,
            "set_by_environment": overridden,
        },
    )


def check_pilot_flags(db: Session) -> Finding:
    """Report which sensitive workflows a deployment has opened.

    Informational by design: any of these may legitimately be on. What must
    not happen is nobody knowing which are.
    """
    flags = {
        name: os.environ.get(name, "")
        for name in (
            "ENABLE_SELF_SERVICE_REGISTRATION",
            "ENABLE_SYNTHETIC_FHIR_UPLOADS",
            "ENABLE_DATA_MARKETPLACE",
            "ENABLE_PATIENT_STUDY_ENROLLMENT",
        )
    }
    on = sorted(k for k, v in flags.items() if v.strip().lower() in {"1", "true", "yes", "on"})
    return Finding(
        "pilot_flags", True, INFO,
        f"{len(on)} sensitive workflow(s) enabled: {', '.join(on) or 'none'}.",
        count=len(on),
        detail={"enabled": on},
    )


def check_secrets_configured(db: Session) -> Finding:
    """A blank or short JWT secret makes every other control decorative."""
    secret = os.environ.get("JWT_SECRET", "")
    ok = len(secret) >= 32
    return Finding(
        "secrets_configured", ok, BLOCKER,
        "JWT secret is set and of adequate length."
        if ok else
        "JWT_SECRET is missing or shorter than 32 characters. "
        "Tokens are forgeable; every authorization check downstream is void.",
        # Never the value, never the length of a weak secret beyond the verdict.
        detail={"configured": bool(secret)},
    )


INVARIANTS: List[Callable[[Session], Finding]] = [
    check_no_precise_clinical_dates,
    check_no_placeholder_institutions,
    check_completed_exports_were_risk_assessed,
    check_completed_exports_have_manifests,
    check_release_manifests_verify,
    check_releases_had_approvals,
    check_revocations_are_tracked,
    check_no_unapproved_researcher_holds_studies,
    check_export_threshold_not_lowered,
    check_pilot_flags,
    check_secrets_configured,
]


def run_audit(db: Session, checks: List[Callable[[Session], Finding]] = None) -> AuditReport:
    """Run every invariant. A check that raises is reported as a blocker.

    A privacy checker that goes green because it crashed is worse than no
    checker at all, so exceptions are converted into failures rather than
    allowed to abort the run or be swallowed.
    """
    findings: List[Finding] = []
    for check in (checks if checks is not None else INVARIANTS):
        try:
            findings.append(check(db))
        except Exception as exc:
            findings.append(Finding(
                getattr(check, "__name__", "unknown").removeprefix("check_"),
                False, BLOCKER,
                f"Check could not run ({type(exc).__name__}). "
                "An invariant that cannot be evaluated is not satisfied.",
            ))
    return AuditReport(findings)
