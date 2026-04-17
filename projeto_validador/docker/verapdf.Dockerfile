# Sprint C — validador-verapdf container
#
# Multi-stage build baseado no Dockerfile oficial do veraPDF, mas adaptado para Debian (glibc)
# para compatibilidade com python:3.11-slim.
#
#   Stage 1 (verapdf-installer): eclipse-temurin:11-jdk — instala VeraPDF via IzPack (Debian)
#   Stage 2 (runtime): python:3.11-slim + JRE 11 copiado de Stage 1
#
# VeraPDF greenfield 1.26.5 — open-source PDF/X-4 validator.
# https://github.com/veraPDF/veraPDF-apps

# ── Stage 1: Install VeraPDF com Java 11 (Debian-based) ───────────────────────
FROM eclipse-temurin:11-jdk AS verapdf-installer

ENV VERAPDF_VERSION=1.26.5

# Copiar o XML de instalação automatizada (formato oficial do projeto)
COPY docker/docker-install.xml /tmp/docker-install.xml

RUN apt-get update && apt-get install -y --no-install-recommends wget unzip \
    && wget -q "https://software.verapdf.org/releases/1.26/verapdf-greenfield-${VERAPDF_VERSION}-installer.zip" \
         -O /tmp/verapdf-installer.zip \
    && unzip -q /tmp/verapdf-installer.zip -d /tmp \
    && java -jar /tmp/verapdf-greenfield-${VERAPDF_VERSION}/verapdf-izpack-installer-${VERAPDF_VERSION}.jar \
         /tmp/docker-install.xml \
    && rm -rf /tmp/verapdf*.zip /tmp/verapdf-greenfield-${VERAPDF_VERSION}

# ── Stage 2: Python + VeraPDF runtime (Debian) ────────────────────────────────
FROM python:3.11-slim

# Copy JRE from stage 1 (Debian -> Debian compatibility)
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"
COPY --from=verapdf-installer /opt/java/openjdk ${JAVA_HOME}

# Copy installed VeraPDF from stage 1
COPY --from=verapdf-installer /opt/verapdf /opt/verapdf
ENV PATH="/opt/verapdf:${PATH}"

# ── System deps for Python packages ──────────────────────────────────────────
# libvips and others are needed if workers use them
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps (same as main app) ───────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# ── Healthcheck ───────────────────────────────────────────────────────────────
# AC4: verapdf --version must return 0 at container start
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD verapdf --version || exit 1

# ── Celery worker — queue:verapdf only ───────────────────────────────────────
CMD ["celery", "-A", "workers.celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=1", \
     "-Q", "queue:verapdf"]
