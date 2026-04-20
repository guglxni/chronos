FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY chronos/ chronos/
COPY scripts/ scripts/

CMD ["uvicorn", "chronos.main:app", "--host", "0.0.0.0", "--port", "8100"]
