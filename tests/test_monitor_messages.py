"""A probe must report what happened, not what it would have meant.

scripts/monitor.py is the thing that wakes someone up, and scripts/alert.py
turns its lines into the body of a GitHub issue. So a message that names a
cause the probe never established is worse than a vague one: it sends an
operator looking for a broken build when the event was a connection reset.

This was found live. A deploy probe reported

    [FAIL] app_shell_renders: HTTP 0 — root element not found

on a request that never completed. Nothing was known about the root element;
the HTTP 0 beside the claim was the only hint that the message was wrong.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from monitor import describe_failure  # noqa: E402


def test_a_failed_request_is_not_reported_as_a_missing_element():
    """The message that prompted this."""
    message = describe_failure(0, "URLError: The handshake operation timed out",
                               "root element not found")
    assert "request failed" in message
    assert "root element" not in message
    assert "handshake" in message


def test_a_real_200_without_the_element_still_says_so():
    message = describe_failure(200, "<html><body>nope</body></html>",
                               "root element not found")
    assert message == "HTTP 200 — root element not found"


def test_the_status_is_carried_for_any_other_response():
    assert describe_failure(503, "upstream down", "the app shell did not load") \
        == "HTTP 503 — the app shell did not load"


def test_the_exception_text_is_bounded():
    """An alerting issue body should not swallow a megabyte of traceback."""
    message = describe_failure(0, "X" * 5000, "root element not found")
    assert len(message) < 250


def test_only_a_200_is_read_as_the_spa_capturing_api_routes():
    """A 500 is the API failing — a different outage with a different fix.

    Reporting it as the SPA swallowing /api would point the fix at the
    rewrite rules, which are not what is broken.
    """
    captured = describe_failure(200, "<html>", "the SPA is capturing /api routes")
    failing = describe_failure(500, "boom", "unexpected status for an unknown API path")
    assert "SPA is capturing" in captured
    assert "SPA" not in failing
