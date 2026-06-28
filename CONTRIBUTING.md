# Contributing to FinBuddy

Thanks for your interest in improving FinBuddy! 🎉 This guide explains how to
set up the project and the conventions we follow.

## Code of Conduct

By participating you agree to uphold our
[Code of Conduct](./CODE_OF_CONDUCT.md). Please be kind.

## Project layout

```
backend/   FastAPI + aiogram + SQLAlchemy (async) + Alembic
frontend/  React + Vite Telegram Mini App
```

## Local setup

### Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # fill BOT_TOKEN (and optionally GROQ_API_KEY)
docker compose up -d db       # Postgres (run from repo root)
alembic upgrade head
uvicorn app.main:app --reload
```

> Use **Python 3.12**. Newer interpreters may lack prebuilt wheels for pinned
> dependencies.

Run the tests and linter before opening a PR:

```bash
pytest
ruff check .
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env          # set VITE_API_BASE_URL
npm run dev
```

To develop the Mini App in a normal browser, capture an `initData` string from
Telegram and paste it into `VITE_DEV_INIT_DATA`.

## Pull requests

1. Fork and create a feature branch: `git checkout -b feat/my-change`.
2. Keep changes focused and add tests where it makes sense.
3. Ensure `pytest`, `ruff check .` and `npm run build` all pass.
4. Use clear, conventional commit messages (e.g. `feat:`, `fix:`, `docs:`).
5. Open a PR describing the motivation and the change.

## Reporting bugs & ideas

Open an issue with steps to reproduce (for bugs) or a short proposal (for
features). Screenshots and example messages help a lot.

## Security

Please do **not** open public issues for security problems. See
[SECURITY.md](./SECURITY.md).
