"""
OpenLLMetry (Traceloop SDK) initialization.

Sets up vendor-neutral LLM observability via OpenTelemetry, exporting traces
to the configured OTLP endpoint (Langfuse, Jaeger, etc.).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from chronos.config.settings import settings

logger = logging.getLogger("chronos.observability")

Traceloop: Any = None

try:
    from traceloop.sdk import Traceloop as _Traceloop

    Traceloop = _Traceloop
except ImportError:
    pass


def setup_openllmetry() -> None:
    """
    Initialize OpenLLMetry via the Traceloop SDK.

    - In development mode, batching is disabled for immediate trace visibility.
    - Fails silently if the SDK is not installed or the endpoint is unreachable,
      so that CHRONOS can operate in environments without a tracing backend.
    """
    if not settings.otel_exporter_otlp_endpoint:
        logger.info("OTEL endpoint not configured — skipping OpenLLMetry setup")
        return

    if Traceloop is None:
        logger.warning(
            "traceloop-sdk not installed — OpenLLMetry disabled. "
            "Install with: pip install traceloop-sdk"
        )
        return

    try:
        # Required for gen_ai semantic conventions in OpenTelemetry >= 1.28
        os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental")
        Traceloop.init(
            app_name=settings.otel_service_name,
            api_endpoint=settings.otel_exporter_otlp_endpoint,
            # Disable batching in development for real-time trace visibility
            disable_batch=settings.environment == "development",
        )
        logger.info(
            "OpenLLMetry initialized: service=%s, endpoint=%s",
            settings.otel_service_name,
            settings.otel_exporter_otlp_endpoint,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        logger.warning(
            "OpenLLMetry setup failed (non-fatal): %s. CHRONOS will continue without LLM tracing.",
            exc,
        )
