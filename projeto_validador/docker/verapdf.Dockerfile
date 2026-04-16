# Sprint C — validador-verapdf container
#
# Combines OpenJDK 17 (for VeraPDF CLI) with Python 3.11 (for Celery worker).
# This container is the only service that has a JVM — isolated to keep cold-start
# fast for the main workers.
#
# VeraPDF greenfield 1.24.x — open-source PDF/X-4 validator (reference implementation).
# https://github.com/veraPDF/veraPDF-apps

FROM python:3.11-slim

# ── System deps ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# ── VeraPDF CLI ───────────────────────────────────────────────────────────────
ENV VERAPDF_VERSION=1.26.2
RUN wget -q \
        "https://github.com/veraPDF/veraPDF-apps/releases/download/v${VERAPDF_VERSION}/verapdf-greenfield-${VERAPDF_VERSION}.zip" \
        -O /tmp/verapdf.zip \
    && unzip -q /tmp/verapdf.zip -d /opt \
    && mv "/opt/verapdf-greenfield-${VERAPDF_VERSION}" /opt/verapdf \
    && chmod +x /opt/verapdf/verapdf \
    && rm /tmp/verapdf.zip

ENV PATH="/opt/verapdf:$PATH"

# ── Python deps (same as main app) ───────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# ── Healthcheck ───────────────────────────────────────────────────────────────
# AC4: verapdf --version must return 0 at container start
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD verapdf --version || exit 1

# ── Celery worker — queue:verapdf only ───────────────────────────────────────
CMD ["celery", "-A", "workers.celery_app", "worker",
     "--loglevel=info",
     "--concurrency=1",
     "-Q", "queue:verapdf"]
