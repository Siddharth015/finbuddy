# FinBuddy

[![CI](https://github.com/your-org/finbuddy/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/finbuddy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

An AI-powered personal & shared finance assistant on Telegram. Log expenses in
natural shorthand (`1000-zomato`), track investments and bank accounts, and open
an in-Telegram dashboard with smart insights and monthly reports. Built for solo
users and couples who want a shared budget with clean personal/shared separation.

## Features

- **Quick expense capture** — type `1000-zomato` in chat; the bot parses,
  auto-categorizes, and (in shared spaces) asks how to split it.
- **Spaces** — a budget container shared by one or more users. Couples join the
  same Space via an invite deep link and see one dashboard.
- **Personal vs Shared segregation** — every transaction has a `scope` and an
  optional split, powering `Mine / Shared` views and a live "who owes whom"
  settlement.
- **Bank accounts & balances** — track multiple accounts and cash; balances
  update automatically as you log income/expenses.
- **Investments** — track holdings (equity, MF, FD, crypto, gold) with live P&L.
- **Spending insights** — category donut, daily trend, and anomaly detection.
- **AI monthly report** — Groq (Llama 3.3) generated summary + savings advice,
  with a deterministic offline fallback so it works without an API key.
- **Telegram Mini App** — a polished React dashboard that authenticates using
  signed Telegram `initData` (no passwords).

## Architecture

```
Telegram ──► aiogram bot ─┐
Mini App  ──► React (Vite) ┴─► FastAPI ─► PostgreSQL
                                  └─► Groq (Llama 3.3) for AI insights
```

One FastAPI service hosts both the Telegram webhook and the Mini App REST API.
Authentication for the Mini App verifies the HMAC of Telegram `initData`
against the bot token, so the server never trusts a client-supplied user id.

## Project layout

```
backend/   FastAPI + aiogram + SQLAlchemy (async) + Alembic
  app/
    models/        ORM models (users, spaces, accounts, transactions, …)
    schemas/       Pydantic request/response models
    services/      parser, categorizer, settlement, analytics, AI, CRUD
    api/           REST routers
    bot/           aiogram handlers & keyboards
    security.py    Telegram initData validation
    main.py        FastAPI app + webhook/polling lifespan
  alembic/         migrations
  tests/           unit + end-to-end API tests
frontend/  React + Vite Telegram Mini App
docker-compose.yml
```

## Quick start (local)

You need **Python 3.12**, **Node 18+**, and Docker (for Postgres).

### 1. Create a Telegram bot

Talk to [@BotFather](https://t.me/BotFather), create a bot, and copy the token.
(Optional) grab a free `GROQ_API_KEY` from https://console.groq.com for AI
reports.

### 2. Backend

```bash
cp backend/.env.example backend/.env       # set BOT_TOKEN (and GROQ_API_KEY)

docker compose up -d db                     # start Postgres

cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                        # create tables
uvicorn app.main:app --reload               # bot (long polling) + API
```

The bot now responds in Telegram. Try messaging it `1000-zomato`,
`+50000 salary`, or `/balance`.

### 3. Mini App (frontend)

```bash
cp frontend/.env.example frontend/.env      # set VITE_API_BASE_URL
cd frontend
npm install
npm run dev
```

Host the built frontend over HTTPS and set `MINIAPP_URL` in `backend/.env` so the
bot shows an **Open Dashboard** button. In BotFather you can also register the
Mini App URL as the bot's menu button.

### Run everything with Docker

```bash
cp backend/.env.example backend/.env        # fill in secrets
docker compose up --build
# API → http://localhost:8000, Mini App → http://localhost:5173
```

## Production webhooks

Set `WEBHOOK_URL` to your public HTTPS base URL. On startup the app registers a
Telegram webhook at `<WEBHOOK_URL>/telegram/webhook` (validated with
`WEBHOOK_SECRET`) instead of long polling.

## Configuration

| Variable           | Description                                               |
| ------------------ | --------------------------------------------------------- |
| `BOT_TOKEN`        | Telegram bot token from BotFather (required)              |
| `WEBHOOK_URL`      | Public HTTPS base URL; enables webhook mode in prod       |
| `WEBHOOK_SECRET`   | Shared secret validating webhook calls                    |
| `DATABASE_URL`     | Async SQLAlchemy URL (Postgres)                           |
| `GROQ_API_KEY`     | Groq key for AI reports (optional; falls back gracefully) |
| `AI_MODEL`         | Groq model id (default `llama-3.3-70b-versatile`)         |
| `CORS_ORIGINS`     | Comma-separated allowed origins for the API               |
| `MINIAPP_URL`      | HTTPS URL of the Mini App (adds Open Dashboard button)    |
| `DEFAULT_CURRENCY` | ISO 4217 currency for new spaces (default `INR`)          |

## Bot commands

| Command         | Description                  |
| --------------- | ---------------------------- |
| `1000-zomato`   | Log an expense in shorthand  |
| `+50000 salary` | Log income                   |
| `/balance`      | Quick monthly snapshot       |
| `/report`       | AI summary & savings tips    |
| `/invite`       | Share your space with others |
| `/dashboard`    | Open the Mini App            |
| `/help`         | Show help                    |

## Testing & linting

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
pytest

cd ../frontend
npm run build      # type-checks and builds
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) and our
[Code of Conduct](./CODE_OF_CONDUCT.md). For security reports, see
[SECURITY.md](./SECURITY.md).

## License

[MIT](./LICENSE) — free to use, modify and ship.

## Disclaimer

FinBuddy is a personal finance tracker, not regulated financial advice.
