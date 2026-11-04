# ==============================================================================
# RegQuest ML Microservice — Production Dockerfile
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Create non-privileged user for security
RUN groupadd -r regquest && useradd -r -g regquest -d /app -s /sbin/nologin regquest

# Copy installed python wheels from builder
COPY --from=builder /root/.local /app/.local
ENV PATH=/app/.local/bin:$PATH

# Copy application code and serialized model artifacts ONLY
# Note: Raw data CSV files are explicitly excluded via .dockerignore to safeguard PII
COPY app/ /app/ML/app/
COPY src/ /app/ML/src/
COPY artifacts/ /app/ML/artifacts/
COPY requirements.txt /app/ML/requirements.txt
COPY README.md /app/ML/README.md

ENV PYTHONPATH=/app
ENV PORT=8001
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

USER regquest

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "ML.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

