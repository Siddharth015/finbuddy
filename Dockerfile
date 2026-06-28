# syntax=docker/dockerfile:1
# ----------------------------------------------------------------------------
# FinBuddy production image: single container that serves the REST API, the
# Telegram webhook, and the Mini App dashboard from one HTTPS origin.
# ----------------------------------------------------------------------------

# --- Stage 1: build the React Mini App --------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
# Empty base URL => the app calls the API on its own origin (relative /api/...).
ENV VITE_API_BASE_URL=""
RUN npm run build

# --- Stage 2: Python backend ------------------------------------------------
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    FRONTEND_DIST=/app/frontend_dist

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
# Built Mini App assets, served by FastAPI (see app/main.py).
COPY --from=frontend /web/dist ./frontend_dist

COPY backend/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
CMD ["/usr/local/bin/entrypoint.sh"]
