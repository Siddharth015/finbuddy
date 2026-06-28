"""FastAPI application: hosts the Telegram webhook and the Mini App REST API.

In production (``WEBHOOK_URL`` set) Telegram pushes updates to ``/telegram/webhook``.
In local development the app long-polls in a background task instead.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from aiogram.types import BotCommand, Update
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.bot import get_bot, get_dispatcher
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finbuddy")

_WEBHOOK_PATH = "/telegram/webhook"

_BOT_COMMANDS = [
    BotCommand(command="dashboard", description="Open your visual dashboard"),
    BotCommand(command="balance", description="This month's snapshot"),
    BotCommand(command="wealth", description="Savings, investments & net worth"),
    BotCommand(command="report", description="AI summary & savings tips"),
    BotCommand(command="invite", description="Share a space with your partner"),
    BotCommand(command="help", description="How FinBuddy works"),
]


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    bot = get_bot(settings.bot_token)
    dispatcher = get_dispatcher()
    polling_task: asyncio.Task | None = None

    with contextlib.suppress(Exception):
        await bot.set_my_commands(_BOT_COMMANDS)

    if settings.use_webhook:
        webhook_url = settings.effective_webhook_url + _WEBHOOK_PATH
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.effective_webhook_secret,
            drop_pending_updates=True,
        )
        logger.info("Webhook registered at %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        polling_task = asyncio.create_task(dispatcher.start_polling(bot))
        logger.info("Started Telegram long polling")

    try:
        yield
    finally:
        if polling_task is not None:
            polling_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await polling_task
        if settings.use_webhook:
            with contextlib.suppress(Exception):
                await bot.delete_webhook()
        await bot.session.close()


app = FastAPI(
    title="FinBuddy API",
    description="AI-powered personal & shared finance assistant for Telegram.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(_WEBHOOK_PATH, include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if (
        settings.effective_webhook_secret
        and x_telegram_bot_api_secret_token != settings.effective_webhook_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret token"
        )
    bot = get_bot(settings.bot_token)
    dispatcher = get_dispatcher()
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}


# --- Mini App (single-origin) -------------------------------------------------
# When a built frontend is present, serve it from this same service so one HTTPS
# origin hosts the API, the Telegram webhook, and the dashboard (no CORS needed).
_dist = Path(settings.frontend_dist) if settings.frontend_dist else None
if _dist and _dist.is_dir():
    _assets = _dist / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")
    logger.info("Serving Mini App from %s", _dist)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str) -> FileResponse:
        candidate = _dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
