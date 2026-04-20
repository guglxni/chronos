"""
OpenLLMetry (Traceloop SDK) initialization.

Sets up vendor-neutral LLM observability via OpenTelemetry, exporting traces
to the configured OTLP endpoint (Langfuse, Jaeger, etc.).
"""

from __future__ import annotations

import logging

from chronos.config.settings import settings

logger = logging.getLogger("chronos.observability")


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

    try:
        from traceloop.sdk import Traceloop  # type: ignore

        Traceloop.init(
            app_name=settings.otel_service_name,
            api_endpoint=settings.otel_exporter_otlp_endpoint,
            # Disable batching in development for real-time trace visibility
            disable_batch=settings.environment == "development",
        )
        logger.info(
            f"OpenLLMetry initialized: service={settings.otel_service_name}, "
            f"endpoint={settings.otel_exporter_otlp_endpoint}"
        )
    except ImportError:
        logger.warning(
            "traceloop-sdk not installed — OpenLLMetry disabled. "
            "Install with: pip install traceloop-sdk"
        )
    except Exception as exc:
        logger.warning(
            f"OpenLLMetry setup failed (non-fatal): {exc}. "
            "CHRONOS will continue without LLM tracing."
        )
