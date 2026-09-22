#!/usr/bin/env python3
"""Probe a running HealthDB deployment and fail loudly when it is not serving.

Written after an outage in which every /api route returned
FUNCTION_INVOCATION_FAILED while the site itself still rendered. The
deployment looked fine. Nothing was watching the part that had broken.

So this checks behaviour, not liveness:

* the health route reports a reachable database, not merely HTTP 200;
* a real API route returns data;
* an unknown API path returns 404 — if the SPA rewrite starts swallowing
  /api, every endpoint silently becomes an HTML page with a 200, which is
  the worst possible failure because nothing looks wrong;
* the deployed revision is reported, so a "fixed" deploy that never shipped
  is visible.

With ADMIN_TOKEN set it also runs the server-side invariants, turning this
from an uptime check into a safety check.

Usage:
    python scripts/monitor.py https://healthdb.ai
    ADMIN_TOKEN=... python scripts/monitor.py https://healthdb.ai
Exit status is 0 only when every probe passes.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

TIMEOUT_SECONDS = 20


def fetch(url, token=None):
    """Return (status, body, seconds). Network failure is a status of 0."""
    request = urllib.request.Request(url, headers={"User-Agent": "healthdb-monitor"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.read().decode("utf-8", "replace"), time.monotonic() - started
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), time.monotonic() - started
    except Exception as exc:
        return 0, f"{type(exc).__name__}: {exc}", time.monotonic() - started


def describe_failure(status, body, diagnosis):
    """Say what actually happened, not what it would have meant.

    A probe that failed because the request never completed has established
    nothing about the thing it was checking. Reporting "root element not
    found" for a connection reset sends an operator looking for a broken
    build at three in the morning, when the event was a network blip — and
    these strings become the body of an alerting issue, so a confident wrong
    diagnosis is worse than a vague right one.

    `status` of 0 means the request itself failed; `body` then holds the
    exception rather than a response.
    """
    if status == 0:
        return f"request failed — {body[:160]}"
    return f"HTTP {status} — {diagnosis}"


class Probes:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.failures = []

    def report(self, name, ok, detail):
        print(f"[{'ok  ' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            self.failures.append(name)

    def health(self):
        status, body, seconds = fetch(f"{self.base}/api/health")
        if status != 200:
            return self.report("health", False, f"HTTP {status} — {body[:200]}")
        try:
            payload = json.loads(body)
        except ValueError:
            # An HTML body here means the SPA rewrite captured /api/health.
            return self.report("health", False, f"non-JSON response — {body[:120]}")
        connected = payload.get("database") == "connected"
        self.report(
            "health", connected,
            f"database={payload.get('database')} "
            f"revision={payload.get('revision')} in {seconds:.2f}s",
        )
        return payload

    def api_route_serves(self):
        status, body, seconds = fetch(f"{self.base}/api/institutions")
        ok = status == 200 and body.lstrip().startswith(("[", "{"))
        self.report("api_route_serves", ok,
                    f"HTTP {status} in {seconds:.2f}s" if ok
                    else f"HTTP {status} — {body[:120]}")

    def unknown_api_path_is_404(self):
        """The SPA must never answer for /api. A 200 here is a silent outage."""
        status, body, _ = fetch(f"{self.base}/api/definitely-not-a-route")
        ok = status == 404
        self.report("unknown_api_path_is_404", ok,
                    "unknown API path 404s as expected" if ok
                    # Only a 200 is the signature of the SPA answering for
                    # /api. A 500 is the API failing, which is a different
                    # outage with a different fix.
                    else describe_failure(
                        status, body,
                        "the SPA is capturing /api routes" if status == 200
                        else "unexpected status for an unknown API path"))

    def app_shell_renders(self):
        status, body, seconds = fetch(self.base + "/")
        ok = status == 200 and "<div id=\"root\"" in body
        self.report("app_shell_renders", ok,
                    f"HTTP {status} in {seconds:.2f}s" if ok
                    else describe_failure(
                        status, body,
                        "root element not found" if status == 200
                        else "the app shell did not load"))

    def invariants(self, token):
        status, body, _ = fetch(f"{self.base}/api/health/invariants", token=token)
        if status in (401, 403):
            return self.report("invariants", False,
                               f"HTTP {status} — ADMIN_TOKEN is not an admin token")
        try:
            payload = json.loads(body)
        except ValueError:
            return self.report("invariants", False, f"non-JSON response — {body[:120]}")
        self.report("invariants", bool(payload.get("ok")),
                    payload.get("summary", f"HTTP {status}"))
        for finding in payload.get("findings", []):
            if not finding.get("passed"):
                print(f"         - {finding['name']}: {finding['summary']}")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    probes = Probes(argv[1])
    print(f"Probing {probes.base}")
    probes.health()
    probes.api_route_serves()
    probes.unknown_api_path_is_404()
    probes.app_shell_renders()

    token = os.environ.get("ADMIN_TOKEN")
    if token:
        probes.invariants(token)
    else:
        print("[skip] invariants: set ADMIN_TOKEN to run server-side safety checks")

    print()
    if probes.failures:
        print(f"MONITOR FAILED: {', '.join(probes.failures)}")
        return 1
    print("MONITOR OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
