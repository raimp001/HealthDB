"""Where a record came from, recorded without pointing back at a person.

Data whose origin is unknown cannot be appraised. A researcher looking at a
stage value needs to know whether it came from a structured oncology module,
a free-text note somebody parsed, or a patient typing it in — those are not
the same evidence, and treating them as one number is how a real-world
evidence study quietly becomes fiction. A patient asking "where did this come
from?" deserves an answer too, because control over data you cannot trace is
not really control.

The obvious implementation is the wrong one. Storing the source system's
record identifier — a FHIR resource id, an MRN, an encounter number — creates
exactly the linkage key the rest of this pipeline exists to destroy. Anyone
holding the source system could match a released row straight back to the
patient it came from.

So provenance here answers *what kind of thing this is and how it was
interpreted*, never *which record it was*:

* `source_system`  — the class of source, not the institution
* `resource_type`  — what the source called it
* `parser`/`parser_version` — what interpreted it, so a later mapping bug can
  be scoped to the records it touched
* `source_digest`  — a salted hash of the raw resource, for integrity and
  duplicate detection, which never leaves the server
* `ingested_at`    — when it arrived

The digest is deliberately salted with a server-side secret. An unsalted hash
of a FHIR resource is a confirmation oracle: an adversary holding a candidate
record could hash it and test for a match. Salting removes that while keeping
the property we actually need, which is that two ingests of the same resource
agree with each other.

`exportable()` is the split that matters. Source system and parser version
travel with a release, because a researcher needs them to appraise the data.
The digest never does.
"""
import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any, Mapping, Optional

# Bumped when the parsing or de-identification behaviour changes in a way that
# alters what a record means. It is stored per record so that a mapping fixed
# in March can be traced to precisely the rows parsed before it.
PARSER = "healthdb.fhir_ingest"
PARSER_VERSION = "1"

# Sources this pilot can actually receive from. A value outside this set is
# recorded as "unknown" rather than echoed, so a caller cannot write arbitrary
# text into a provenance field that a researcher will later read as fact.
KNOWN_SOURCE_SYSTEMS = frozenset({
    "synthetic_fhir_bundle",
    "patient_entered",
    "seed_fixture",
    "unknown",
})


def _digest_key() -> bytes:
    """Server-side salt for source digests.

    Falls back to the JWT secret rather than to a constant: an unsalted digest
    would let anyone holding a candidate source resource confirm whether it is
    in the database.
    """
    return (os.environ.get("PROVENANCE_SALT")
            or os.environ.get("JWT_SECRET", "")).encode() or b"healthdb-unsalted"


def source_digest(raw: Any) -> str:
    """A stable, salted fingerprint of the source resource.

    Same resource in, same digest out, so duplicates are detectable. Without
    the salt it is not reproducible, so it is useless as a linkage key to
    anyone who does not already hold the database.
    """
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(_digest_key(), canonical.encode(), hashlib.sha256).hexdigest()


def build(
    *,
    source_system: str,
    resource_type: Optional[str] = None,
    raw: Any = None,
    ingested_at: Optional[datetime] = None,
) -> dict:
    """Describe a record's origin, carrying nothing that points to a person."""
    if source_system not in KNOWN_SOURCE_SYSTEMS:
        source_system = "unknown"
    return {
        "source_system": source_system,
        "resource_type": str(resource_type)[:60] if resource_type else None,
        "parser": PARSER,
        "parser_version": PARSER_VERSION,
        "source_digest": source_digest(raw) if raw is not None else None,
        "ingested_at": (ingested_at or datetime.utcnow()).isoformat(),
    }


def exportable(provenance: Optional[Mapping[str, Any]]) -> dict:
    """The part of provenance a researcher may see.

    System, type, parser and arrival — enough to appraise the data and to
    scope a later mapping fix. Never the digest: inside the server it is an
    integrity check, but handed to a recipient it becomes a key for matching
    released rows against a source system they may also hold.
    """
    if not provenance:
        return {"source_system": "unknown", "parser_version": None}
    return {
        "source_system": provenance.get("source_system", "unknown"),
        "resource_type": provenance.get("resource_type"),
        "parser_version": provenance.get("parser_version"),
        "ingested_at": provenance.get("ingested_at"),
    }


def describe_for_patient(provenance: Optional[Mapping[str, Any]]) -> str:
    """One plain sentence answering "where did this come from?"."""
    system = (provenance or {}).get("source_system", "unknown")
    return {
        "synthetic_fhir_bundle": "Imported from a health record file you uploaded.",
        "patient_entered": "Entered by you directly.",
        "seed_fixture": "Example data created for testing this platform.",
        "unknown": "Origin not recorded. This record predates provenance tracking.",
    }.get(system, "Origin not recorded.")


def summarize(provenances) -> dict:
    """Which kinds of source contributed to a release, and how many records.

    Counts by system only. A release manifest should say what the data is
    made of; it must not become a per-record trace back to its origins.
    """
    counts: dict = {}
    versions = set()
    for entry in provenances:
        system = (entry or {}).get("source_system", "unknown")
        counts[system] = counts.get(system, 0) + 1
        version = (entry or {}).get("parser_version")
        if version:
            versions.add(str(version))
    return {
        "records_by_source_system": dict(sorted(counts.items())),
        "parser_versions": sorted(versions),
    }
