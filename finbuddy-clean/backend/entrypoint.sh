#!/usr/bin/env sh
# Apply database migrations, then launch the API + bot.
# PORT is provided by the hosting platform (Render, Railway, Fly, ...).
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FinBuddy on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
