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

print("SMOKE OK")
