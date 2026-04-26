"""
FastAPI middleware for request logging and global error handling.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from chronos.config.settings import settings

logger = logging.getLogger("chronos.api")


async def logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log every request with method, path, status code, and duration."""
    start = time.perf_counter()
    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.0fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


async def error_handler(request: Request, exc: Exception) -> Response:
    """Return a JSON error response for any unhandled exception."""
    logger.error(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error"},
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
        },
    )
