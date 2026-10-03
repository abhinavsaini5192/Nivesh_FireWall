# ==============================================================================
# Nivesh Firewall — Production Backend Dockerfile
# Phase 14.5: Deployment, Performance & Production Validation
# ==============================================================================
# Multi-stage secure build for Python FastAPI application.
# Runs as non-root user 'nivesh' with minimal attack surface.
# ==============================================================================

# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a wheelhouse
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -e .

# --- Stage 2: Production Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group
RUN groupadd -g 10001 nivesh && \
    useradd -u 10001 -g nivesh -s /bin/bash -m nivesh

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application source and migration configuration
COPY --chown=nivesh:nivesh nivesh/ /app/nivesh/
COPY --chown=nivesh:nivesh alembic/ /app/alembic/
COPY --chown=nivesh:nivesh alembic.ini /app/alembic.ini
COPY --chown=nivesh:nivesh pyproject.toml /app/pyproject.toml

# Set secure production environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NIVESH_ENV=production \
    NIVESH_DEBUG=False \
    NIVESH_HOST=0.0.0.0 \
    NIVESH_PORT=8000 \
    NIVESH_LOG_FORMAT=json

# Switch to non-root user
USER nivesh:nivesh

# Expose HTTP port
EXPOSE 8000

# Healthcheck probe querying internal liveness endpoint
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/live || exit 1

# Production command launching Uvicorn
CMD ["uvicorn", "nivesh.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-config", "None"]
