import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.routers import experiments
from app.database import check_db_connection
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Robotics Experiment & Diagnostics Platform",
    description="API para ingerir, consultar y diagnosticar experimentos de robótica.",
    version="0.1.0",
)

app.include_router(experiments.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """One structured log line per request: method, path, status, duration.
    This is the first thing you'd check to answer "is the API slow, or is
    it a specific endpoint?" without needing to reproduce the issue.
    """
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(OperationalError)
async def database_unavailable_handler(request: Request, exc: OperationalError):
    # SQLAlchemy raises OperationalError for connection failures (DB down,
    # network partition, etc.) — distinct from a query being wrong. Worth
    # its own 503 (Service Unavailable) rather than a generic 500, so a
    # client/monitor can tell "the API is broken" apart from "the database
    # is temporarily unreachable, retry me".
    logger.error("Database connection failed handling %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"error": "database_unavailable", "detail": "Could not reach the database. Try again shortly."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log the full traceback server-side for debugging, but never leak
    # internals (stack trace, exception message) to the client — that's
    # an information-disclosure risk, not just a UX nicety.
    logger.exception("Unhandled exception handling %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


@app.get("/health")
def health():
    db_ok = check_db_connection()
    status_code = 200 if db_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if db_ok else "degraded", "database": "up" if db_ok else "down"},
    )
