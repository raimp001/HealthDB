"""Refuse a record rather than store one nobody can trust.

Someone hands over their medical history because they hope it will help. If a
value arrives malformed and is stored anyway, it does not sit there harmlessly
— it gets counted in a feasibility search, drawn into a cohort, and averaged
into a finding. Their contribution stops being neutral and starts making the
science worse, which is the exact opposite of why they gave it. And nobody
tells them.

So this checks whether a parsed record is *believable* as clinical data. The
parser already decides whether the shape is right; this decides whether the
content could be true.

Two choices worth defending:

**Quarantine per record, not per upload.** Refusing a whole bundle because one
value is wrong throws away good data and teaches people not to bother. Each
record stands or falls alone, and the upload reports exactly what did not make
it.

**Refuse rather than store-and-flag.** A flag has to be honoured by every
query that comes later, forever, by people who did not write it. A record that
was never stored cannot be read by a query that forgot to check. The flag
approach fails silently; this one fails loudly and early.

The checks are deliberately narrow. This rejects values that cannot be true —
a diagnosis year before modern oncology, an age beyond human lifespan, a
record carrying nothing at all. It does not reject values that are merely
*unusual*, because rare is exactly what a lot of cancer research is looking
for, and a platform that quietly discards outliers is deciding what counts as
a real patient.
"""
from datetime import datetime
from typing import Any, Mapping, Optional

# Nothing earlier is plausible as a dated clinical record in this platform,
# and a future date is a data-entry error rather than a prediction.
EARLIEST_PLAUSIBLE_YEAR = 1900

# HIPAA Safe Harbor already requires ages over 89 to be aggregated, so a value
# beyond this is a parsing failure, not a remarkable patient.
MAX_PLAUSIBLE_AGE = 120


def _numbers_in(value: Any):
    """Every number reachable in a payload, however nested."""
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _numbers_in(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _numbers_in(item)


def _age_values(data: Mapping[str, Any]):
    """Ages, wherever they are recorded, including inside a band."""
    import re

    for key, value in (data or {}).items():
        if "age" not in str(key).lower():
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            yield float(value)
        elif isinstance(value, str):
            # "70-79", "90+", "65" — every bound has to be plausible.
            for match in re.findall(r"\d+", value):
                yield float(match)


def check_record(record: Mapping[str, Any], *, now: Optional[datetime] = None) -> Optional[str]:
    """Why this record cannot be stored, or None if it can.

    The reason is written to be read by the person who contributed it, so it
    says what is wrong rather than naming a field in a schema they have never
    seen.
    """
    now = now or datetime.utcnow()
    data = record.get("data") or {}

    # A record with no content is not a record. Storing it would inflate every
    # count that includes it while carrying nothing.
    if not isinstance(data, Mapping) or not any(
        value not in (None, "", [], {}) for value in data.values()
    ):
        return "This entry contained no readable clinical information."

    year = record.get("original_year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return "The year on this entry could not be read as a year."
        if year < EARLIEST_PLAUSIBLE_YEAR:
            return (f"The year on this entry ({year}) is earlier than this "
                    "platform can treat as a real clinical date.")
        if year > now.year:
            return (f"The year on this entry ({year}) is in the future, which "
                    "usually means a typo in the source record.")

    for age in _age_values(data):
        if age < 0:
            return "An age on this entry was negative."
        if age > MAX_PLAUSIBLE_AGE:
            return (f"An age on this entry ({age:g}) is beyond a human "
                    "lifespan, which usually means a unit or parsing error.")

    return None


def partition(records, *, now: Optional[datetime] = None):
    """Split parsed records into the ones worth keeping and the ones not.

    Returns (accepted, rejected) where each rejected entry is
    (record, reason). Ordering is preserved so a caller can report positions
    a contributor can recognise in their own file.
    """
    accepted, rejected = [], []
    for record in records:
        reason = check_record(record, now=now)
        (rejected.append((record, reason)) if reason else accepted.append(record))
    return accepted, rejected


def describe_rejections(rejected) -> list:
    """What to tell the person who uploaded them.

    Each entry names the kind of record and why it was refused. No field
    paths, no parser internals: someone looking at their own health record
    should be able to tell which entry this is about.
    """
    return [
        {
            "category": record.get("data_category"),
            "type": record.get("data_type"),
            "year": record.get("original_year"),
            "reason": reason,
        }
        for record, reason in rejected
    ]
