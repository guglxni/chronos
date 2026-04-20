"""
FastAPI middleware for request logging and global error handling.
"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger("chronos.api")


async def logging_middleware(request: Request, call_next):
    """Log every request with method, path, status code, and duration."""
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.error(
            f"{request.method} {request.url.path} ERROR {duration_ms:.0f}ms — {exc}",
            exc_info=True,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} {response.status_code} {duration_ms:.0f}ms"
    )
    return response


async def error_handler(request: Request, exc: Exception) -> Response:
    """Return a JSON error response for any unhandled exception."""
    logger.error(
        f"Unhandled error on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
        },
    )
