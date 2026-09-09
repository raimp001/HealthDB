#!/usr/bin/env python3
"""Carry a monitor or audit failure to a person, without teaching them to ignore it.

A red tick in a workflow list is not an alert. Nobody is watching that list at
three in the morning, and the outage this repository already survived was
invisible for hours precisely because the only signal was somewhere nobody
looks.

The hard part is not sending the first message. It is not sending the next
forty. An hourly comment on the same open outage is how a channel becomes
muted, and a muted channel is worse than no channel at all — it looks like
coverage while providing none. So:

* **One issue per outage, not one per check.** A failure opens a tracking
  issue; subsequent failures update it only when what is wrong has changed.
* **Silence while nothing changes.** Same failure, same state, no new comment.
* **Recovery closes it**, with a note. A stale open issue for something long
  since fixed trains people to disbelieve the next one.

Runs on the GITHUB_TOKEN that Actions provides, so it needs no secret anyone
has to set up. An optional ALERT_WEBHOOK_URL gets the same summary if one is
configured.

Usage:
    python scripts/alert.py --state failed --summary "health: HTTP 500"
    python scripts/alert.py --state ok --summary "MONITOR OK"
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# Identifies the tracking issue this script owns. Anything else in the tracker
# is somebody's work and must not be touched.
MARKER = "<!-- healthdb-monitor-alert -->"
TITLE = "Production monitor is failing"
API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Decision logic, kept free of network calls so it can be tested directly.
# ---------------------------------------------------------------------------

def decide(state: str, summary: str, open_issue: dict | None) -> dict:
    """What to do, given the current state and any issue already open.

    Returns {"action": ..., "body": ...} where action is one of:
      open    — nothing is tracking this yet
      comment — the failure changed; say what changed
      quiet   — same failure as last time, say nothing
      close   — recovered
      none    — healthy and nothing was open
    """
    if state == "ok":
        if open_issue:
            return {"action": "close",
                    "body": f"Recovered.\n\n{summary}\n\n{MARKER}"}
        return {"action": "none", "body": ""}

    if not open_issue:
        return {"action": "open",
                "body": f"The production monitor is failing.\n\n{summary}\n\n{MARKER}"}

    # An open issue exists. Only speak if the failure is different from the
    # one already described, otherwise this becomes an hourly drip that
    # everybody filters.
    if summary.strip() and summary.strip() in (open_issue.get("body") or ""):
        return {"action": "quiet", "body": ""}
    return {"action": "comment",
            "body": f"Still failing, and what is failing has changed.\n\n{summary}"}


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def _request(method: str, path: str, token: str, payload=None):
    request = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "healthdb-alert",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode()
    return json.loads(body) if body else {}


def find_open_issue(repo: str, token: str) -> dict | None:
    """The tracking issue this script owns, if it is open.

    Matched on a marker in the body rather than on the title, so renaming the
    issue by hand does not cause a duplicate to be opened alongside it.
    """
    issues = _request("GET", f"/repos/{repo}/issues?state=open&per_page=50", token)
    for issue in issues:
        if MARKER in (issue.get("body") or ""):
            return issue
    return None


def notify_webhook(summary: str, state: str) -> None:
    """Optional. Absent configuration is not an error, it is a choice."""
    url = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        request = urllib.request.Request(
            url, method="POST",
            data=json.dumps({"text": f"[healthdb {state}] {summary}"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(request, timeout=15).read()
    except Exception as exc:
        # A webhook that will not deliver must not stop the issue being
        # raised. Losing the loud channel is not a reason to lose the
        # durable one.
        print(f"webhook delivery failed: {type(exc).__name__}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=("ok", "failed"), required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report the decision without touching the tracker")
    args = parser.parse_args(argv)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required", file=sys.stderr)
        return 2

    open_issue = find_open_issue(repo, token)
    decision = decide(args.state, args.summary, open_issue)
    print(f"alert decision: {decision['action']}")

    if args.dry_run or decision["action"] in ("none", "quiet"):
        return 0

    if decision["action"] == "open":
        _request("POST", f"/repos/{repo}/issues", token,
                 {"title": TITLE, "body": decision["body"]})
    elif decision["action"] == "comment":
        _request("POST", f"/repos/{repo}/issues/{open_issue['number']}/comments",
                 token, {"body": decision["body"]})
    elif decision["action"] == "close":
        _request("POST", f"/repos/{repo}/issues/{open_issue['number']}/comments",
                 token, {"body": decision["body"]})
        _request("PATCH", f"/repos/{repo}/issues/{open_issue['number']}", token,
                 {"state": "closed"})

    notify_webhook(args.summary, args.state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
