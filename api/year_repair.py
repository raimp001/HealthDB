"""Restore the clinical year to records that were stored without one.

This exists because of a specific failure, and the shape of that failure is
worth keeping written down.

The FHIR upload path truncated each source date to a year at the parse
boundary — correctly — and then handed that integer to a second function that
only accepted strings. It returned None for every one of them, so every
imported record was stored with no year at all.

Nothing failed. The column is nullable, and a record with no year is
indistinguishable from a record whose source genuinely never carried a date.
The only visible effect was that anyone who uploaded their records quietly
stopped matching any cohort with a date range on it. They had done the hard
part — consented, connected, handed over their history — and were unreachable
for exactly the studies most likely to want them.

The repair is not an inference. The year is still sitting in the same row, in
the de-identified payload, under ``diagnosis_year``, ``year``, ``start_year``
or ``death_year``, because that is where the parser also put it. This module
copies a value the record already carries into the column that should have
held it. Where the payload carries no year, or carries two that disagree,
nothing is written: a guessed date is worse than a missing one, because a
missing one is honest about itself.
"""
from typing import Any, Mapping, Optional

# A year lives under one of these keys, or any key ending in ``_year``. The
# parser writes exactly one per record; more than one is a signal to stop.
_YEAR_KEY = "year"
_YEAR_SUFFIX = "_year"

# Wider than ingest validation's window on purpose. This decides what is
# recognisable as a year, not what is believable as a clinical date — that
# judgement belongs to api/ingest_validation.py, and duplicating it here
# would mean two places to keep in step.
_MIN_RECOGNISABLE_YEAR = 1000
_MAX_RECOGNISABLE_YEAR = 9999


def year_in_payload(data: Any) -> Optional[int]:
    """The year a record already carries, or None if it carries none or two.

    Returning None for a disagreement is deliberate. Two different years in
    one record means something upstream is wrong, and picking one would bury
    that under a plausible-looking value.
    """
    if not isinstance(data, Mapping):
        return None

    found = set()
    for key, value in data.items():
        name = str(key).lower()
        if name != _YEAR_KEY and not name.endswith(_YEAR_SUFFIX):
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if _MIN_RECOGNISABLE_YEAR <= value <= _MAX_RECOGNISABLE_YEAR:
            found.add(value)

    return found.pop() if len(found) == 1 else None


def repairable(row) -> Optional[int]:
    """The year this stored row should have had, or None to leave it alone.

    Only rows whose stored year is absent are touched. A row that already has
    a year is never overwritten, even if the payload disagrees — this module
    fills gaps, and silently rewriting stored values is how a repair becomes
    a corruption.
    """
    if getattr(row, "original_year", None) is not None:
        return None
    return year_in_payload(getattr(row, "deidentified_data", None))


def survey(rows) -> dict:
    """What a repair would and would not be able to do. Reads only.

    Separating "repairable" from "no year anywhere" matters to whoever reads
    this: the first number shrinks to zero once the repair runs, and the
    second one never will, because those records really have no date.
    """
    missing = repairable_count = 0
    for row in rows:
        if getattr(row, "original_year", None) is not None:
            continue
        missing += 1
        if repairable(row) is not None:
            repairable_count += 1
    return {
        "rows_without_a_year": missing,
        "rows_repairable": repairable_count,
        "rows_with_no_year_recorded_anywhere": missing - repairable_count,
    }
