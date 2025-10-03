## Minimal, clean Docker image for EDUKY-monitor
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends curl ca-certificates \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/eduky-monitor

# Leverage build cache for dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app_v2_fixed.py app_production.py ./
COPY web/ ./web/

# Runtime dirs
RUN mkdir -p web/instance logs /var/log/eduky-monitor

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:5000/ || exit 1

CMD ["python", "app_production.py"]