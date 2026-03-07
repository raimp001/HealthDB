"""
HIPAA Compliance Middleware for FastAPI
Enforces security controls for protected health information (PHI) access.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

audit_logger = logging.getLogger("healthdb.hipaa_audit")


class HIPAAComplianceMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce HIPAA security rules for FastAPI"""

    # Paths that access PHI and require strict auditing
    PHI_PATHS = ["/api/patient", "/api/clinical", "/api/cohort", "/api/data"]

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 1. Enforce HTTPS in production
        if request.headers.get("X-Forwarded-Proto") == "http":
            return Response(
                content='{"detail": "HTTPS required for PHI access"}',
                status_code=403,
                media_type="application/json"
            )

        # 2. Process request
        response = await call_next(request)

        # 3. Add security headers to every response
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # PHI responses should never be cached
        if any(request.url.path.startswith(p) for p in self.PHI_PATHS):
            response.headers["Expires"] = "0"

        # 4. Audit log PHI access
        duration_ms = (time.time() - start_time) * 1000
        if any(request.url.path.startswith(p) for p in self.PHI_PATHS):
            client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not client_ip and request.client:
                client_ip = request.client.host

            auth_header = request.headers.get("Authorization", "")
            has_auth = bool(auth_header)

            audit_logger.info(
                f"PHI_ACCESS: method={request.method} path={request.url.path} "
                f"status={response.status_code} duration_ms={duration_ms:.0f} "
                f"ip={client_ip} authenticated={has_auth}"
            )

        return response
