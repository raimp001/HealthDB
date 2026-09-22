"""Check that a release's stored bytes are still the bytes it promised.

A finding cites a release digest so the result can be reproduced against the
exact data that produced it. `check_release_manifests_verify` already proves a
manifest still hashes to its own digest — but that is the manifest checking
itself. Nothing re-derived the digest of the *file* the manifest describes, so
an extract whose stored content had drifted would keep its intact manifest,
keep its citation, and say nothing.

The distinction this module exists to preserve:

**Unverifiable is not verified.** A release whose file is no longer stored
cannot be checked, and the honest answer is "cannot be checked" — not a pass.
Collapsing the two is the same failure as a record with no date reading
identically to a record whose date was nonsense: both hide a fact behind a
value that looks fine. A reviewer asking "is this finding still backed by its
data?" must be able to tell "yes" from "nobody can say".

So every check returns one of three states, and a caller cannot get a boolean
that quietly averages them.
"""
from dataclasses import dataclass
from typing import Optional

from .release_manifest import digest

VERIFIED = "verified"
MISMATCH = "mismatch"
UNVERIFIABLE = "unverifiable"


@dataclass
class ContentCheck:
    """Whether a release's stored file still matches its recorded digest."""
    release_id: str
    state: str
    recorded_digest: str
    computed_digest: Optional[str] = None

    @property
    def ok(self) -> bool:
        """True only for a positive check.

        Not for unverifiable. A property named `ok` that returned True when
        nothing could be checked would be the exact collapse this module
        exists to prevent.
        """
        return self.state == VERIFIED

    def explain(self) -> str:
        if self.state == VERIFIED:
            return ("The stored extract still hashes to the digest recorded "
                    "when it was released.")
        if self.state == MISMATCH:
            return ("The stored extract no longer hashes to the digest "
                    "recorded when it was released. Any finding citing this "
                    "release cites bytes that have changed.")
        return ("The extract is no longer stored, so this release cannot be "
                "checked against its digest. That is not a pass: nobody can "
                "confirm the data behind a finding citing it.")

    def as_dict(self) -> dict:
        return {
            "release_id": self.release_id,
            "state": self.state,
            "verified": self.ok,
            "recorded_digest": self.recorded_digest,
            "computed_digest": self.computed_digest,
            "explanation": self.explain(),
        }


def verify_content(release, job) -> ContentCheck:
    """Re-derive the digest of the stored extract and compare it.

    `job` may be None, or may carry no file: both mean unverifiable rather
    than failing. A release whose recorded digest is missing is also
    unverifiable — there is nothing to compare against, and treating an
    absent expectation as a met one would be worse than useless.
    """
    recorded = getattr(release, "content_digest", None) or ""
    content = getattr(job, "result_csv", None) if job is not None else None

    if not recorded or content is None:
        return ContentCheck(
            release_id=str(getattr(release, "id", "")),
            state=UNVERIFIABLE,
            recorded_digest=recorded,
        )

    computed = digest(content)
    return ContentCheck(
        release_id=str(release.id),
        state=VERIFIED if computed == recorded else MISMATCH,
        recorded_digest=recorded,
        computed_digest=computed,
    )
