# SUTRA — one image, one process: the console is static, the API is stdlib Python.
#
#   docker build -t sutra .
#   docker run -p 8000:8000 -e PORT=8000 sutra
#
# The container starts the same service used in development; there is no second web server, no CDN,
# and no runtime network egress requirement.

# ── stage 1: build the workbench (the frontend served at /) ─────────────────────────────────────
FROM node:20-alpine AS web
WORKDIR /build/workbench
COPY battle_model/package.json battle_model/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY battle_model/ ./
RUN npm run build

# ── stage 1b: build the reference console (served only if the workbench build is absent) ────────
FROM node:20-alpine AS console
WORKDIR /build/console
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY web/ ./
RUN npm run build

# ── stage 2: runtime ────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app

# the service is standard-library only; no pip install is required at runtime
COPY sutra/ ./sutra/
COPY tools/ ./tools/
COPY tests/ ./tests/
COPY data/ ./data/
COPY --from=web /build/workbench/site ./battle_model/site
COPY --from=console /build/console/site ./web/site

# run as a non-root user; the API is read-only over the store, and /health needs no filesystem writes
RUN useradd --create-home --uid 10001 sutra && chown -R sutra:sutra /app
USER sutra

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=4s --start-period=8s --retries=3 \
  CMD python3 -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health',timeout=3).read()"

CMD ["python3", "tools/serve_runtime.py", "--host", "0.0.0.0"]
