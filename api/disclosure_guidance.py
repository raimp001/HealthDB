"""Name the variable that is blocking an extract, instead of a shrug.

A researcher who reaches the export step has designed a cohort, obtained an
IRB approval and signed a data-use agreement. What they got back was:

    smallest group contains 3 subject(s), minimum 11 required;
    4 subject(s) affected. Export blocked.
    Broaden the cohort or drop identifying variables.

That is advice with no object. Which variable? Broadened how? With half a
dozen requested fields there are many combinations, each one a round trip,
and meanwhile the people who consented are sitting in a cohort nobody can
use. The system already knows the answer — it formed the equivalence classes
— so withholding it is not caution, it is just unhelpfulness.

So this re-measures with one quasi-identifier held out at a time and reports
which single removal would clear the floor.

Three limits, deliberately:

**Only single removals are suggested.** It would be easy to search for the
smallest set of fields whose removal gets an extract through. That is an
optimiser against a privacy control, and a researcher who follows it ends up
with a dataset stripped of the variables their question needed. If no single
removal is enough, the honest answer is that the cohort is too narrow, and
this says so rather than proposing to gut the file.

**Only variables the researcher actually asked for.** Suggesting the removal
of a field that is not in the export is advice that cannot be taken.

**It suggests, it does not act.** Nothing here relaxes a threshold or
coarsens a value. The gate is unchanged; only the error message gets better.
"""
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from .disclosure_risk import DEFAULT_QUASI_IDENTIFIERS, assess_records


@dataclass
class Suggestion:
    """One variable whose removal would clear the k floor."""
    field: str
    resulting_k: int

    def phrase(self) -> str:
        return f"{self.field} (smallest group would become {self.resulting_k})"


def _present_quasi_identifiers(rows, quasi_identifiers) -> list:
    """The quasi-identifiers these rows actually carry.

    Holding out a field no row has would re-measure the same classes and
    report no improvement, which reads as "that would not help" about a
    variable that is not there.
    """
    present = []
    for name in quasi_identifiers:
        if any(name in row or name in (row.get("payload") or {}) for row in rows):
            present.append(name)
    return present


def single_removals_that_clear(
    rows,
    *,
    threshold_k: int,
    quasi_identifiers: Sequence[str] = DEFAULT_QUASI_IDENTIFIERS,
    requested_fields: Optional[Sequence[str]] = None,
    **assess_kwargs,
) -> list:
    """Variables whose removal on its own would bring the extract over the floor.

    Ranked by how much room each leaves, best first. Empty when no single
    removal is enough — which is a finding, not a failure to find one.
    """
    rows = list(rows)
    candidates = _present_quasi_identifiers(rows, quasi_identifiers)
    if requested_fields is not None:
        askable = set(requested_fields)
        candidates = [name for name in candidates if name in askable]

    suggestions = []
    for name in candidates:
        held_out = tuple(q for q in quasi_identifiers if q != name)
        if not held_out:
            continue
        report = assess_records(
            rows, threshold_k=threshold_k, quasi_identifiers=held_out,
            **assess_kwargs,
        )
        if report.min_k >= threshold_k:
            suggestions.append(Suggestion(field=name, resulting_k=report.min_k))

    return sorted(suggestions, key=lambda s: (-s.resulting_k, s.field))


def advise(
    rows,
    *,
    threshold_k: int,
    quasi_identifiers: Sequence[str] = DEFAULT_QUASI_IDENTIFIERS,
    requested_fields: Optional[Sequence[str]] = None,
    with_numbers: bool = True,
    **assess_kwargs,
) -> str:
    """One sentence a researcher can act on.

    ``with_numbers`` is false where the caller is not entitled to counts —
    the design-time preview answers before any study approval exists, and
    reports a verdict rather than measurements. The lever is still named:
    knowing *which* field to change is what makes the verdict useful, and it
    is not a count of anybody.
    """
    suggestions = single_removals_that_clear(
        rows, threshold_k=threshold_k, quasi_identifiers=quasi_identifiers,
        requested_fields=requested_fields, **assess_kwargs,
    )

    if not suggestions:
        return (
            "No single variable accounts for this, so the cohort itself is too "
            "narrow — broadening the criteria is the change to make. Dropping "
            "several variables at once could force it through, but would leave "
            "a dataset unlikely to answer the question you asked."
        )

    if with_numbers:
        listed = ", or ".join(s.phrase() for s in suggestions[:3])
        return f"Removing any one of these would clear the floor: {listed}."

    listed = ", or ".join(s.field for s in suggestions[:3])
    return f"Removing any one of these would be enough on its own: {listed}."
