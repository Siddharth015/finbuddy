"""aiogram bot: dispatcher, bot instance and handler registration."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router

_bot: Bot | None = None
_dispatcher: Dispatcher | None = None


def get_bot(token: str) -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


def get_dispatcher() -> Dispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher()
        _dispatcher.include_router(router)
    return _dispatcher


__all__ = ["get_bot", "get_dispatcher", "router"]
