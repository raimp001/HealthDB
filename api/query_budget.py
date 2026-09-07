"""Stop a cohort count being narrowed until it isolates one person.

Small-cell suppression protects a single query. It does not protect a
sequence of them. A researcher who runs

    "AML patients"                        -> 40
    "AML patients, excluding age 61"      -> 39

has learned that exactly one person in the cohort is 61, and can keep going
until they have that person's full record. Both queries cleared the floor.
Neither was suppressed. The disclosure happened between them.

The defence is to compare each new result set against what the same
researcher has already been told, and refuse a query whose answer differs
from an earlier answer by fewer than the floor. That is the quantity an
attacker subtracts, so that is the quantity that has to be protected.

Two properties worth stating, because they constrain how this is used:

* **It compares sets, not query text.** Rewording a query, reordering its
  filters or arriving at the same people by another route changes nothing.
  The identity of a result is who is in it.
* **It is per researcher.** Two researchers each running one query have
  disclosed nothing to either. Collusion between accounts is a different
  threat, and this does not address it.

A history is finite, so this is a mitigation and not a proof. An attacker
willing to wait out the window, or to use several accounts, is not stopped
by it. What it stops is the easy version, which is currently trivial.
"""
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set

# How many of a researcher's recent result sets each new query is compared
# against. Every comparison is a set operation over ids already in memory, so
# this is cheap; the limit exists to bound storage, not CPU.
DEFAULT_HISTORY_DEPTH = 50


@dataclass
class DifferencingRisk:
    """A prior answer that this one is too close to."""
    prior_query_id: str
    prior_count: int
    new_count: int
    difference: int
    threshold: int

    def message(self) -> str:
        return (
            f"This cohort differs from one of your earlier results by only "
            f"{self.difference} patient(s), below the floor of {self.threshold}. "
            "Comparing the two would identify those individuals, so the count "
            "is withheld. Change the criteria more substantially, or ask for "
            "the narrower cohort directly."
        )


def _as_set(patient_ids: Iterable) -> Set[str]:
    return {str(pid) for pid in patient_ids}


def find_differencing_risk(
    patient_ids: Iterable,
    history: Sequence,
    *,
    threshold: int,
) -> Optional[DifferencingRisk]:
    """Return the first prior result this one is too close to, or None.

    `history` holds objects with `id` and `patient_set`. A prior result whose
    symmetric difference from the new one is non-empty but smaller than
    `threshold` is a disclosure: subtracting the two counts reveals a group
    too small to hide in.

    An identical result set is not a risk. Re-running the same query tells the
    researcher nothing they were not already told, and refusing it would make
    the tool unusable while protecting nobody.
    """
    new_set = _as_set(patient_ids)
    for prior in history:
        prior_set = _as_set(prior.patient_set or [])
        difference = len(new_set ^ prior_set)
        if 0 < difference < threshold:
            return DifferencingRisk(
                prior_query_id=str(prior.id),
                prior_count=len(prior_set),
                new_count=len(new_set),
                difference=difference,
                threshold=threshold,
            )
    return None


def recent_history(db, model, user_id: str, depth: int = DEFAULT_HISTORY_DEPTH) -> List:
    """The result sets this researcher has most recently been shown."""
    return db.query(model).filter(
        model.user_id == user_id
    ).order_by(model.created_at.desc()).limit(depth).all()


def prune_history(db, model, user_id: str, depth: int = DEFAULT_HISTORY_DEPTH) -> int:
    """Drop this researcher's oldest entries beyond `depth`.

    The history is a record of what a person has already been told, kept only
    to answer the next query. Holding it forever would be its own retention
    problem, so it is bounded.
    """
    keep = {
        str(row.id) for row in db.query(model.id).filter(
            model.user_id == user_id
        ).order_by(model.created_at.desc()).limit(depth).all()
    }
    stale = db.query(model).filter(
        model.user_id == user_id, ~model.id.in_(keep)
    ).all() if keep else []
    for row in stale:
        db.delete(row)
    return len(stale)
