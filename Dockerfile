# Self-hosted PUBLIC DEMO image for aven.
#
# Serves the React UI and the FastAPI planning API from one container, using
# seeded demo data only. It contacts no Databricks service and holds no
# secrets, so it is safe to run on a public URL.
#
# It is NOT the challenge submission artifact: live Databricks evidence
# (AI Search, Lakebase, challenge data) requires the Databricks Apps
# deployment described in docs/databricks-team-handoff.md.

# ---- Stage 1: build the React bundle -----------------------------------
FROM node:24-alpine AS frontend

WORKDIR /build

# Copy manifests first so dependency install caches independently of source.
COPY apps/referral-copilot/package.json apps/referral-copilot/package-lock.json ./
COPY apps/referral-copilot/frontend/package.json ./frontend/
RUN npm ci

COPY apps/referral-copilot/frontend ./frontend
RUN npm run build


# ---- Stage 2: Python runtime -------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Demo dependency set only (~25 MB). The live-mode packages are deliberately
# absent; every import of them in src/backend/* is guarded and degrades to
# demo mode. See apps/referral-copilot/requirements-demo.txt.
COPY apps/referral-copilot/requirements-demo.txt ./
RUN pip install --no-cache-dir -r requirements-demo.txt

COPY apps/referral-copilot/src ./src
COPY apps/referral-copilot/run_app.py ./
COPY --from=frontend /build/frontend/dist ./frontend/dist

# Anonymous, per-session demo identity. This image must never run in
# databricks auth mode: off-platform there is no Databricks proxy, so
# X-Forwarded-User would be attacker-supplied and would forge any owner.
ENV AVEN_AUTH_MODE=local_demo \
    AVEN_ALLOW_LOCAL_DEMO=true

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 aven && chown -R aven:aven /app
USER aven

EXPOSE 8000

# Hosts inject their own $PORT (Render/Railway) or expect 7860 (HF Spaces).
CMD ["sh", "-c", "exec uvicorn src.backend.api:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
