"""Inline keyboards used by the bot."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from app.config import settings


def split_keyboard(txn_id: int) -> InlineKeyboardMarkup:
    """Ask how a freshly-logged expense should be attributed."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🙋 Mine", callback_data=f"scope:{txn_id}:personal"
                ),
                InlineKeyboardButton(
                    text="👥 Shared", callback_data=f"scope:{txn_id}:shared"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete", callback_data=f"del:{txn_id}"
                ),
            ],
        ]
    )


def undo_keyboard(txn_id: int) -> InlineKeyboardMarkup:
    """A single undo button so a mistaken entry can be removed from chat."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Undo", callback_data=f"del:{txn_id}"
                ),
            ],
        ]
    )


def dashboard_keyboard() -> InlineKeyboardMarkup | None:
    """Open-the-Mini-App button. Requires an HTTPS Mini App URL."""
    url = settings.effective_miniapp_url
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Open Dashboard", web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )
