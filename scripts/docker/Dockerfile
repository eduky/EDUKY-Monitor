# Multi-stage build for EDUKY-monitor
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies
COPY ../../requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/eduky-monitor

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source
COPY ../../app_v2_fixed.py ./
COPY ../../run_app.py ./
COPY ../../migrate_database.py ./
COPY ../../web/ ./web/

# Create runtime directories
RUN mkdir -p web/instance logs /var/log/eduky-monitor \
    && chown -R appuser:appuser /opt/eduky-monitor

# Switch to non-root user
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/ || exit 1

CMD ["python", "run_app.py"]