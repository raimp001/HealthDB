"""A failed start has to be able to say where it failed.

When api.main cannot be imported, the serverless platform answers every
route with FUNCTION_INVOCATION_FAILED and nothing else. The traceback exists
only in the host's logs. An outage sat in that state for days because the
one line that explained it was somewhere nobody at hand could read.

api/entry.py imports the application inside a guard and, on failure, serves
a stand-in whose health check reports the exception type and the repository
frames it was raised in. These tests hold two lines: the report is enough to
find the fault, and it never repeats the exception's message, which can
carry a connection string or a fragment of a secret into a public response.
"""
import asyncio
import json

from api.entry import describe_failure, failed_start_app


def raised(exc_factory):
    try:
        raise exc_factory()
    except BaseException as exc:  # noqa: BLE001 - the point is to capture it
        return exc


def call(app, path):
    """Drive an ASGI app once and return (status, parsed body)."""
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app({"type": "http", "path": path, "method": "GET",
                     "headers": []}, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent
                    if m["type"] == "http.response.body")
    return status, json.loads(body)


SECRET = "postgresql://admin:hunter2@db.internal.example/health"


def test_the_report_names_the_type_and_where_it_was_raised():
    detail = describe_failure(raised(lambda: RuntimeError("boom")))
    assert detail["status"] == "failed_to_start"
    assert detail["error_type"] == "RuntimeError"
    assert any("tests/test_entrypoint.py" in frame for frame in detail["raised_at"])


def test_the_report_never_repeats_the_exception_message():
    """A message can carry a connection string. This response is public."""
    detail = describe_failure(raised(lambda: RuntimeError(f"cannot reach {SECRET}")))
    serialized = json.dumps(detail)
    for fragment in ("hunter2", "db.internal.example", "postgresql://", "admin"):
        assert fragment not in serialized, f"report leaks {fragment!r}"


def test_a_missing_module_is_named():
    """Without the name, "ModuleNotFoundError" says nothing — and a package
    name is not a secret."""
    exc = raised(lambda: ModuleNotFoundError("No module named 'psycopg'",
                                             name="psycopg"))
    assert describe_failure(exc)["missing_module"] == "psycopg"


def test_the_python_version_is_reported():
    """A runtime that moved under the application is one of the causes this
    has to be able to reveal."""
    detail = describe_failure(raised(lambda: RuntimeError("x")))
    assert detail["python"].count(".") == 2


def test_the_stand_in_answers_health_with_the_report():
    detail = describe_failure(raised(lambda: RuntimeError(SECRET)))
    status, body = call(failed_start_app(detail), "/api/health")
    assert status == 503
    assert body["status"] == "failed_to_start"
    assert body["error_type"] == "RuntimeError"
    assert "hunter2" not in json.dumps(body)


def test_other_routes_fail_plainly_and_point_at_health():
    """A broken API must not look like an empty one."""
    detail = describe_failure(raised(lambda: RuntimeError("x")))
    status, body = call(failed_start_app(detail), "/api/patient/profile")
    assert status == 503
    assert "/api/health" in body["detail"]
    assert "error_type" not in body


def test_a_healthy_start_is_the_real_application():
    import api.entry as entry
    import api.main as main

    assert entry.startup_failure is None
    assert entry.app is main.app


def test_the_deployment_routes_the_api_through_the_entry_point():
    """The guard only helps if it is the thing the platform invokes."""
    import pathlib

    config = json.loads(
        (pathlib.Path(__file__).resolve().parents[1] / "vercel.json").read_text())
    api_rewrites = [r for r in config["rewrites"] if r["source"] == "/api/(.*)"]
    assert api_rewrites and api_rewrites[0]["destination"] == "/api/entry.py"
