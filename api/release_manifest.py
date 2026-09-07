"""Immutable record of what a research release actually contained.

An extract is a snapshot of a moving database. Without a record of exactly
what left, three things are impossible:

* **Reproducibility.** A result cannot be checked against its inputs if
  nobody can say which rows those inputs were. "The cohort as of last March"
  is not a dataset.
* **Accountability.** When a patient revokes consent, the obligation runs to
  whoever already holds their data. That question has no answer unless the
  holder and the contents were recorded at the time.
* **Metering.** Any future licensing rests on a defensible count of what was
  supplied to whom, under which approvals.

A manifest answers all three, so it is one record rather than three. It is
written once, at release, and never updated: the mutable facts about a
release (downloads, withdrawal) live in separate columns so the hashed
content stays fixed.

The digests are integrity checks, not signatures. They detect a manifest that
no longer matches the file it describes; they do not prove who created it.
Signing would need a key this deployment does not have.
"""
import hashlib
import json
from typing import Any, Mapping, Sequence

# Bumped when the manifest field set changes, so an old manifest is never
# silently re-hashed under new rules and reported as tampered.
MANIFEST_SCHEMA_VERSION = 1


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize deterministically so the same content always hashes alike.

    Sorted keys and fixed separators: dict ordering, whitespace and locale
    must not change the digest.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def digest(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def build_manifest(
    *,
    job_id: str,
    study_id: str,
    study_name: str,
    released_to: str,
    released_at: str,
    variables: Sequence[str],
    subject_count: int,
    record_count: int,
    content_digest: str,
    cohort_criteria: Mapping[str, Any] | None,
    disclosure_risk: Mapping[str, Any] | None,
    approvals: Sequence[Mapping[str, Any]],
    deidentification_level: str,
) -> dict:
    """The hashed content of a release.

    Every field here is a fact about the release itself. Nothing that can
    change afterwards belongs in this dictionary.
    """
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "job_id": job_id,
        "study_id": study_id,
        "study_name": study_name,
        "released_to": released_to,
        "released_at": released_at,
        "deidentification_level": deidentification_level,
        # Sorted so a reordered selection does not read as a different release.
        "variables": sorted(variables),
        "subject_count": subject_count,
        "record_count": record_count,
        "content_digest": content_digest,
        "cohort_criteria": cohort_criteria,
        "disclosure_risk": disclosure_risk,
        "approvals": sorted(
            [dict(a) for a in approvals],
            key=lambda a: (str(a.get("document_type")), str(a.get("id"))),
        ),
    }


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    return digest(canonical_json(manifest))


def verify_manifest(manifest: Mapping[str, Any], expected_digest: str) -> bool:
    """True when the manifest still hashes to the digest recorded at release.

    A false result means the stored manifest has been altered since release,
    or was written under a different schema version. Either way it can no
    longer be cited as evidence of what was supplied.
    """
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        return False
    return manifest_digest(manifest) == expected_digest
