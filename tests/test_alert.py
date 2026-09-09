"""Alerting that a person will still trust on the fortieth hour.

Sending the first message is easy. Not sending the next forty is the whole
problem: an hourly comment on the same open outage is how a channel gets
muted, and a muted channel looks like coverage while providing none.

So these are mostly tests about staying quiet, and about not leaving a stale
open issue behind — the two ways an alert stops being believed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from alert import MARKER, decide  # noqa: E402


def open_issue(body):
    return {"number": 7, "body": body + "\n" + MARKER}


# ---------------------------------------------------------------------------
# Raising it
# ---------------------------------------------------------------------------

def test_a_first_failure_opens_a_tracking_issue():
    decision = decide("failed", "health: HTTP 500", None)
    assert decision["action"] == "open"
    assert "health: HTTP 500" in decision["body"]
    assert MARKER in decision["body"], "the marker is how it finds this issue again"


def test_a_repeat_of_the_same_failure_says_nothing():
    """The test that matters. Forty identical comments is how this gets muted."""
    decision = decide("failed", "health: HTTP 500", open_issue("health: HTTP 500"))
    assert decision["action"] == "quiet"
    assert decision["body"] == ""


def test_a_changed_failure_speaks_up():
    """Same outage, different symptom — that is new information."""
    decision = decide("failed", "database: unavailable", open_issue("health: HTTP 500"))
    assert decision["action"] == "comment"
    assert "database: unavailable" in decision["body"]
    assert "has changed" in decision["body"]


def test_whitespace_alone_does_not_count_as_a_change():
    decision = decide("failed", "  health: HTTP 500  ", open_issue("health: HTTP 500"))
    assert decision["action"] == "quiet"


# ---------------------------------------------------------------------------
# Standing down
# ---------------------------------------------------------------------------

def test_recovery_closes_the_issue():
    """A stale open issue trains people to disbelieve the next one."""
    decision = decide("ok", "MONITOR OK", open_issue("health: HTTP 500"))
    assert decision["action"] == "close"
    assert "Recovered" in decision["body"]


def test_a_healthy_check_with_nothing_open_does_nothing():
    assert decide("ok", "MONITOR OK", None)["action"] == "none"


def test_recovery_is_still_announced_before_closing():
    """Closing silently leaves nobody knowing it is over."""
    decision = decide("ok", "MONITOR OK", open_issue("health: HTTP 500"))
    assert "MONITOR OK" in decision["body"]


# ---------------------------------------------------------------------------
# It must only ever touch its own issue
# ---------------------------------------------------------------------------

def test_the_marker_is_carried_on_everything_it_opens_or_closes():
    """Anything without the marker is somebody's work, not this script's."""
    assert MARKER in decide("failed", "x", None)["body"]
    assert MARKER in decide("ok", "x", open_issue("x-different"))["body"]


def test_an_empty_summary_still_raises_rather_than_silently_passing():
    """A failure with no detail is still a failure."""
    assert decide("failed", "", None)["action"] == "open"


def test_an_empty_summary_against_an_open_issue_does_not_go_quiet():
    """Empty text is in every string. It must not be read as 'unchanged'."""
    decision = decide("failed", "", open_issue("health: HTTP 500"))
    assert decision["action"] == "comment"
