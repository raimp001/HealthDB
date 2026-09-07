"""What a person's contribution actually did.

A points balance is a lie told politely. It says "thank you" in a currency
nobody wants, to someone who gave their medical history because they hoped it
would matter. The honest answer to "what did my data do?" is not a number
that goes up. It is a chain: you gave this, it reached here, it stopped here.

So this builds the chain, and it tells the truth about where the chain stops.

    contributed  ->  searched  ->  enrolled  ->  released  ->  published

Four things this module refuses to do, because each one is how a record stops
being a person:

* **It does not inflate.** A stage that has not happened is reported as not
  happened. No "coming soon", no progress bar implying inevitability. Most
  contributions stop at `contributed`, and that is the truth most people will
  read.
* **It does not blame the contributor.** The chain stops for reasons that have
  nothing to do with them — no study has asked, the cohort was too small, the
  IRB has not approved. Say which, so a person is not left assuming their data
  was not good enough.
* **It does not promise.** Nothing here says a finding is coming. Research
  mostly does not produce findings, and a platform that implies otherwise is
  selling hope back to people who are short of it.
* **It counts nothing it cannot show.** Every number here resolves to
  something the person can look at.

The zero state is the most important screen in this file. Most people will
only ever see that one, and it has to leave them feeling that their decision
was respected rather than filed.
"""
from dataclasses import dataclass, field
from typing import List, Optional

# The stages, in order. A person's contribution reaches the furthest stage
# for which something real exists.
STAGES = ("contributed", "searched", "enrolled", "released", "published")


@dataclass
class Stage:
    """One link in the chain, and whether it actually happened."""
    key: str
    reached: bool
    headline: str
    detail: str
    # Why the chain stops here, when it does. Never the contributor's fault.
    blocked_because: Optional[str] = None
    items: List[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "key": self.key, "reached": self.reached,
            "headline": self.headline, "detail": self.detail,
            "blocked_because": self.blocked_because,
            "items": self.items,
        }


def _record_summary(db, patient_id: str) -> dict:
    from .models import ExtractedMedicalData

    records = db.query(ExtractedMedicalData).filter(
        ExtractedMedicalData.patient_id == patient_id
    ).all()
    years = sorted({r.original_year for r in records if r.original_year})
    categories = sorted({r.data_category for r in records if r.data_category})
    return {
        "record_count": len(records),
        "categories": categories,
        "first_year": years[0] if years else None,
        "last_year": years[-1] if years else None,
    }


def _consent_active(db, patient_id: str) -> bool:
    from .models import Consent

    return db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.consent_type == "research_data_sharing",
        Consent.status == "active",
    ).count() > 0


def build_contribution(db, patient_id: str) -> dict:
    """The full chain for one person, honestly reported.

    Reads only. Everything returned is about this one contributor; nothing
    here reveals another participant, a cohort's contents, or a researcher's
    unpublished work.
    """
    from .models import CohortQueryLog, DataRelease, Study, StudyEnrollment, StudyResult

    patient_id = str(patient_id)
    summary = _record_summary(db, patient_id)
    consented = _consent_active(db, patient_id)
    stages: List[Stage] = []

    # ---- 1. contributed ---------------------------------------------------
    has_records = summary["record_count"] > 0
    span = ""
    if summary["first_year"]:
        span = (f" spanning {summary['first_year']}"
                + (f"–{summary['last_year']}"
                   if summary["last_year"] != summary["first_year"] else ""))
    stages.append(Stage(
        "contributed", has_records,
        f"{summary['record_count']} record{'' if summary['record_count'] == 1 else 's'} contributed"
        if has_records else "No records contributed yet",
        (f"Covering {', '.join(summary['categories'])}{span}. "
         "Dates are stored as a year only — never a month or a day.")
        if has_records else
        "Once you connect a record source, what you contribute will be listed here.",
        blocked_because=None if has_records else "Nothing has been contributed yet.",
        items=[{"category": c} for c in summary["categories"]],
    ))

    # ---- 2. searched ------------------------------------------------------
    # Feasibility searches are how researchers learn which questions can be
    # asked at all. Being counted in one is a real contribution even when no
    # data ever leaves — and for most people this is as far as it goes.
    #
    # The query log is pruned, so this is a count of recent searches, not a
    # lifetime total. It is described that way rather than rounded up.
    searched = sum(
        1 for row in db.query(CohortQueryLog).all()
        if patient_id in {str(s) for s in (row.patient_set or [])}
    )
    stages.append(Stage(
        "searched", searched > 0,
        f"Counted in {searched} recent feasibility search{'' if searched == 1 else 'es'}"
        if searched else "Not yet counted in a feasibility search",
        "Researchers ask whether a question can be answered before they design "
        "a study. Your records were part of those answers. No one saw your "
        "data — only whether enough people like you exist."
        if searched else
        "When a researcher asks whether a question is answerable, your records "
        "will be part of that count. They will not see your data to do it.",
        blocked_because=(
            None if searched else
            "No researcher has run a search your records matched yet."
            if consented else
            "Searches only count records under an active consent."
        ),
    ))

    # ---- 3. enrolled ------------------------------------------------------
    enrollments = db.query(StudyEnrollment).filter(
        StudyEnrollment.patient_id == patient_id,
        StudyEnrollment.status == "enrolled",
    ).all()
    study_ids = [str(e.study_id) for e in enrollments]
    studies = db.query(Study).filter(Study.id.in_(study_ids)).all() if study_ids else []
    stages.append(Stage(
        "enrolled", bool(studies),
        f"Joined {len(studies)} stud{'y' if len(studies) == 1 else 'ies'}"
        if studies else "Not enrolled in a study",
        "A study has to clear ethics review and sign a data agreement before "
        "it can see anything you contributed."
        if studies else
        "Studies you join will appear here. Joining is a separate decision "
        "from contributing, and you can leave one without leaving the other.",
        blocked_because=None if studies else "No study has enrolled you yet.",
        items=[{"study_name": s.name} for s in studies],
    ))

    # ---- 4. released ------------------------------------------------------
    releases = [
        r for r in db.query(DataRelease).all()
        if patient_id in {str(s) for s in (r.subject_ids or [])}
    ]
    downloaded = [r for r in releases if (r.download_count or 0) > 0]
    withdrawn = [r for r in releases if r.withdrawal_required_at is not None]
    stages.append(Stage(
        "released", bool(releases),
        f"Included in {len(releases)} data release{'' if len(releases) == 1 else 's'}"
        if releases else "Your data has not left the platform",
        (f"{len(downloaded)} of these {'has' if len(downloaded) == 1 else 'have'} "
         "been downloaded by the study team. Every release is recorded with a "
         "fingerprint, so what left can always be identified."
         + (f" {len(withdrawn)} carries a withdrawal request from your revoked consent."
            if withdrawn else ""))
        if releases else
        "Nothing you contributed has been sent to a researcher. Releases are "
        "measured for re-identification risk first, and blocked if the group "
        "is too small to hide in.",
        blocked_because=(
            None if releases else
            "No approved study has drawn an extract containing your records."
        ),
        items=[{
            "study_id": str(r.study_id),
            "released_at": r.released_at.isoformat() if r.released_at else None,
            "downloaded": (r.download_count or 0) > 0,
            "content_digest": r.content_digest,
            "withdrawal_required": r.withdrawal_required_at is not None,
        } for r in releases],
    ))

    # ---- 5. published -----------------------------------------------------
    results = db.query(StudyResult).filter(
        StudyResult.study_id.in_(study_ids)
    ).order_by(StudyResult.published_at.desc()).all() if study_ids else []
    stages.append(Stage(
        "published", bool(results),
        f"{len(results)} finding{'' if len(results) == 1 else 's'} published"
        if results else "No findings published yet",
        "This is what your records helped produce."
        if results else
        "Most research does not reach a published finding, and the ones that "
        "do take years. If a study you joined publishes something, it will "
        "appear here — and if it never does, this will keep saying so.",
        blocked_because=(
            None if results else
            "No study you joined has published a finding."
            if studies else
            "A finding can only come from a study you have joined."
        ),
        items=[{"title": r.title, "study_id": str(r.study_id),
                "published_at": r.published_at.isoformat()} for r in results],
    ))

    reached = [s for s in stages if s.reached]
    furthest = reached[-1].key if reached else None

    return {
        "stages": [s.as_dict() for s in stages],
        "furthest_stage": furthest,
        "consent_active": consented,
        # No points, no tier, no score. There is no number here that stands in
        # for a person's contribution, and there should never be one.
        "summary": _summary_line(furthest, consented),
    }


def _summary_line(furthest: Optional[str], consented: bool) -> str:
    """One sentence a person reads first. It has to be true.

    Written so the most common outcome — contributed, nothing further — reads
    as a kept promise rather than a dead end, without implying more is coming.
    """
    if furthest is None:
        return (
            "You have not contributed any records yet."
            if not consented else
            "Your consent is on file. Nothing has been contributed against it yet."
        )
    return {
        "contributed": (
            "Your records are held and available to approved research. No "
            "researcher has drawn on them yet, and you will see it here when "
            "one does."
        ),
        "searched": (
            "Your records have helped researchers work out which questions can "
            "be answered. No one has seen your data."
        ),
        "enrolled": (
            "You have joined a study. Nothing has been sent to its team yet."
        ),
        "released": (
            "An extract containing your records has gone to an approved study "
            "team. You can see exactly which, and when."
        ),
        "published": (
            "Research your records contributed to has produced a published "
            "finding."
        ),
    }[furthest]
