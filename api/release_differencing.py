"""Hold an extract that could be subtracted from one already released.

Small-cell suppression protects a single file. It does not protect a pair of
them. Two extracts whose subject sets differ by three people identify those
three to anyone holding both, and each file on its own cleared every check.

api/query_budget.py defends the same property for cohort *counts*, and its
docstring explains why it refuses to block across accounts: two researchers
studying one disease produce overlapping cohorts by nature, and a control
that fires on ordinary work is one people learn to route around. That
reasoning is right about counts. It does not carry to releases.

A count is cheap, frequent, and exploratory — blocking one interrupts
thinking. A release is rare, already gated by an IRB approval and a signed
DUA, and it is the moment row-level data about real people leaves the
system. It is also the only step here that cannot be undone. So releases get
the expensive control that counts cannot afford: hold, and let a named person
decide.

Three things this deliberately does:

**It holds rather than refuses.** A refusal with no way forward teaches
researchers that the platform is an obstacle and that the way to do science
is to get the data out some other way. A hold says: this needs a second look,
and someone is looking.

**It tells the requester nothing about the collision.** Not which cohort, not
how close, not whose. That detail is exactly what an adversary would want,
and the requester is the one person who must not have it. It goes to the
reviewer instead.

**It counts an identical set as no risk.** Re-running an extract that returns
the same people discloses nothing new, and holding it would protect nobody
while making the tool feel broken.
"""
from dataclasses import dataclass
from typing import Optional, Sequence

from .release_manifest import canonical_json, digest


@dataclass
class ReleaseCollision:
    """A prior release this one is close enough to be subtracted from."""
    prior_release_id: str
    prior_subject_count: int
    new_subject_count: int
    difference: int
    threshold: int
    same_account: bool
    same_study: bool
    prior_downloaded: bool

    def shape(self) -> str:
        """What kind of collision this is, so a reviewer can triage quickly.

        A researcher re-extracting their own study after two more people
        enrolled is not the same event as two accounts arriving at nearly the
        same cohort, and a reviewer should not have to work out which they are
        looking at.
        """
        if self.same_account and self.same_study:
            return "same researcher, same study"
        if self.same_account:
            return "same researcher, different study"
        return "different accounts"

    def for_reviewer(self) -> dict:
        return {
            "prior_release_id": self.prior_release_id,
            "prior_subject_count": self.prior_subject_count,
            "new_subject_count": self.new_subject_count,
            "subjects_differing": self.difference,
            "threshold": self.threshold,
            "shape": self.shape(),
            "prior_release_downloaded": self.prior_downloaded,
        }

    def for_requester(self) -> str:
        """What the person who asked for the extract is told.

        Deliberately carries no number and names no other work. "Within 3
        subjects of another cohort" would hand the requester the quantity this
        control exists to withhold, and would disclose that the other cohort
        exists at all.
        """
        return (
            "This extract is held for disclosure review before it can be "
            "released. Releases are compared against earlier ones, because two "
            "files that differ by only a few subjects can identify those "
            "people to anyone holding both. A reviewer will decide and you "
            "will see the outcome here. Nothing is wrong with your study or "
            "your approvals, and there is nothing for you to correct."
        )


def subject_digest(subject_ids) -> str:
    """Fingerprint of the exact people in a release.

    A reviewer approves a set of subjects, not a job name. If the data moves
    between the review and the release, the approval no longer describes who
    would be released, and this is what makes that detectable rather than
    assumed away — the same reasoning the export approvals use for a cohort
    definition.
    """
    return digest(canonical_json({"subjects": sorted(str(s) for s in subject_ids or [])}))


def find_collision(
    subject_ids,
    prior_releases: Sequence,
    *,
    threshold: int,
    requester_user_id: str = None,
    study_id: str = None,
) -> Optional[ReleaseCollision]:
    """The first prior release this one could be subtracted from, or None.

    `prior_releases` are DataRelease rows, newest first. The comparison is on
    who is in the set, so rewording a cohort or reaching the same people by
    another route changes nothing.
    """
    new_set = {str(s) for s in subject_ids or []}
    for prior in prior_releases:
        prior_set = {str(s) for s in (prior.subject_ids or [])}
        difference = len(new_set ^ prior_set)
        if not 0 < difference < threshold:
            continue
        return ReleaseCollision(
            prior_release_id=str(prior.id),
            prior_subject_count=len(prior_set),
            new_subject_count=len(new_set),
            difference=difference,
            threshold=threshold,
            same_account=(requester_user_id is not None
                          and str(prior.released_to_user_id) == str(requester_user_id)),
            same_study=(study_id is not None
                        and str(prior.study_id) == str(study_id)),
            # Whether anyone actually holds the other file. It does not change
            # the decision to hold — a release that has not been downloaded
            # yet still can be — but a reviewer should know.
            prior_downloaded=bool(getattr(prior, "download_count", 0) or 0),
        )
    return None
