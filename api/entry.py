"""The serverless entry point: the real app, or an honest account of why not.

When api.main fails to import, the platform answers every route with
FUNCTION_INVOCATION_FAILED and nothing else. The traceback exists only in
the host's logs, so anyone without access to those — an operator on a phone,
a monitor, a patient wondering why their portal is blank — learns only that
something is wrong. An outage in November 2026 sat in exactly that state for
days: the cause was one line in a log nobody at hand could open.

This module imports the real application inside a guard. If the import
succeeds it is the application, unchanged. If it fails, a minimal ASGI app
takes its place and /api/health answers 503 with *where* the failure was
raised.

What it deliberately does not say is the exception's message. A message can
carry a connection string, a hostname or a fragment of a secret, and this
answer is public. The exception type, the Python version and the repository
frames (file, line, function) are enough to find the fault and reveal
nothing that is not already in the public source. The full traceback still
goes to stderr for whoever can read the host's logs.

Uses the standard library only, so it keeps working when the failure is a
missing or broken dependency.
"""
import json
import os
import sys
import traceback

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def describe_failure(exc: BaseException) -> dict:
    """Where a failed start was raised, with nothing sensitive in it."""
    frames = []
    for frame in traceback.extract_tb(exc.__traceback__):
        path = os.path.abspath(frame.filename)
        if path.startswith(_REPO_ROOT + os.sep):
            frames.append(
                f"{os.path.relpath(path, _REPO_ROOT)}:{frame.lineno} in {frame.name}"
            )
    detail = {
        "status": "failed_to_start",
        "error_type": type(exc).__name__,
        "raised_at": frames[-3:],
        "python": ".".join(str(part) for part in sys.version_info[:3]),
    }
    # The one piece of an exception that is both safe and indispensable: a
    # missing module's name is a package name, not a secret, and without it
    # "ModuleNotFoundError" says nothing.
    if isinstance(exc, ImportError) and getattr(exc, "name", None):
        detail["missing_module"] = str(exc.name)
    return detail


def failed_start_app(detail: dict):
    """A minimal ASGI app that reports a failed start instead of crashing."""
    health = json.dumps(detail).encode()
    other = json.dumps({
        "detail": "The API failed to start. /api/health reports where.",
    }).encode()

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        body = health if scope.get("path", "").rstrip("/") == "/api/health" else other
        await send({
            "type": "http.response.start",
            "status": 503,
            "headers": [
                (b"content-type", b"application/json"),
                (b"cache-control", b"no-store"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})

    return app


def load():
    """The real application, or a stand-in that says why it is absent."""
    try:
        from .main import app as real_app
        return real_app, None
    except BaseException as exc:  # a library calling sys.exit() counts too
        traceback.print_exc()
        detail = describe_failure(exc)
        print(f"API failed to start: {json.dumps(detail)}", file=sys.stderr)
        return failed_start_app(detail), detail


app, startup_failure = load()
