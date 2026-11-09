#!/usr/bin/env python3
"""Boot the app the way the serverless runtime does, then serve requests.

Importing cleanly is not the same as serving successfully. A migration that
takes a lock at import time passes an import check and still times out under
concurrent cold starts, which is how a deploy once returned
FUNCTION_INVOCATION_FAILED on every request while every test was green.

Run: python scripts/smoke_boot.py
"""
import os
import sys
import time
import traceback

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET", "smoke-only-secret")
# Explicit, because the implicit fallback this used to rely on is the thing
# a real deployment must never do: serve an empty per-instance file in place
# of the configured database. Production without DATABASE_URL is now a
# degraded boot, which phase two below checks on purpose.
if not os.environ.get("DATABASE_URL"):
    import tempfile
    os.environ["DATABASE_URL"] = (
        "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="healthdb-smoke-"),
                                    "smoke.db"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUDGET_SECONDS = 10.0

start = time.time()
try:
    import api.main as main
except Exception:
    traceback.print_exc()
    print("FAIL: module import raised")
    sys.exit(1)

elapsed = time.time() - start
print(f"import completed in {elapsed:.2f}s")
if elapsed > BUDGET_SECONDS:
    print(f"FAIL: import took longer than {BUDGET_SECONDS}s; a cold start would risk timing out")
    sys.exit(1)

from fastapi.testclient import TestClient  # noqa: E402

failures = []
with TestClient(main.app) as client:
    for path in ["/api/health", "/api/stats/platform", "/api/institutions",
                 "/api/stats/cancer-types"]:
        response = client.get(path)
        print(f"  {path}: HTTP {response.status_code}")
        if response.status_code >= 500:
            failures.append(f"{path} -> {response.status_code}: {response.text[:160]}")

if failures:
    print("FAIL: endpoints returned 5xx")
    for f in failures:
        print("  ", f)
    sys.exit(1)


# Phase two: production configuration with no database at all.
#
# This is the shape of a real outage. The API returned
# FUNCTION_INVOCATION_FAILED on every route while the static site served,
# because api.database fell through to a local SQLite file when DATABASE_URL
# was unset and the serverless filesystem is read-only, so mkdir raised while
# the module was still being imported — before the app existed and before the
# health check could say anything.
#
# Booting is the requirement, not connecting: an API that cannot reach its
# database should still start and report why. A fresh interpreter, because
# the modules above are already imported with a database configured.
import subprocess  # noqa: E402

probe = """
import os, sys
sys.path.insert(0, "__ROOT__")
os.environ["ENVIRONMENT"] = "production"
os.environ["JWT_SECRET"] = "smoke-only-secret"
os.environ.pop("DATABASE_URL", None)
import api.main as main
from fastapi.testclient import TestClient
with TestClient(main.app) as client:
    response = client.get("/api/health")
print("SMOKE_STATUS=" + str(response.status_code))
print("SMOKE_REASON=" + str((response.json() or {}).get("reason", "")))
""".replace("__ROOT__", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

result = subprocess.run([sys.executable, "-c", probe],
                        capture_output=True, text=True, timeout=120)
# Startup prints to stdout, so read the markers rather than a line number.
marked = dict(
    line.split("=", 1) for line in result.stdout.splitlines()
    if line.startswith(("SMOKE_STATUS=", "SMOKE_REASON="))
)
if result.returncode != 0 or "SMOKE_STATUS" not in marked:
    print("FAIL: production without DATABASE_URL did not boot")
    print(result.stderr[-900:])
    sys.exit(1)

status, reason = marked["SMOKE_STATUS"], marked.get("SMOKE_REASON", "")
print(f"  no-database boot: HTTP {status}")
if status != "503":
    print(f"FAIL: expected a degraded health check, got {status}")
    sys.exit(1)
if "DATABASE_URL" not in reason:
    print("FAIL: the degraded health check did not say what was wrong")
    print("  reason:", reason or "(empty)")
    sys.exit(1)
print("  no-database boot reports:", reason[:90])

print("SMOKE OK")
