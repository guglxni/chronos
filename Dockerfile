FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY chronos/ chronos/
COPY scripts/ scripts/

RUN pip install --no-cache-dir . && \
    useradd -m -u 1000 chronos && \
    chown -R chronos /app

USER chronos

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-8100}/api/v1/health" || exit 1

CMD ["sh", "-c", "uvicorn chronos.main:app --host 0.0.0.0 --port ${PORT:-8100}"]
