"""Validate Telegram Mini App ``initData`` per the official algorithm.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(ValueError):
    """Raised when initData is missing, malformed, or fails verification."""


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str
    username: str | None = None
    language_code: str | None = None


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def validate_init_data(
    init_data: str, bot_token: str, *, max_age_seconds: int = 86_400
) -> TelegramUser:
    """Verify the HMAC of ``initData`` and return the embedded user.

    Raises :class:`InitDataError` on any problem.
    """
    if not init_data:
        raise InitDataError("Missing initData")
    if not bot_token:
        raise InitDataError("Server bot token not configured")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("initData missing hash")

    data_check_string = "\n".join(
        f"{key}={pairs[key]}" for key in sorted(pairs)
    )
    secret = _secret_key(bot_token)
    expected_hash = hmac.new(
        secret, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataError("initData signature mismatch")

    auth_date = pairs.get("auth_date")
    if auth_date and max_age_seconds > 0:
        try:
            age = time.time() - int(auth_date)
        except ValueError as exc:
            raise InitDataError("Invalid auth_date") from exc
        if age > max_age_seconds:
            raise InitDataError("initData has expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("initData missing user")
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("Invalid user payload") from exc

    if "id" not in user or "first_name" not in user:
        raise InitDataError("Incomplete user payload")

    return TelegramUser(
        id=int(user["id"]),
        first_name=str(user["first_name"]),
        username=user.get("username"),
        language_code=user.get("language_code"),
    )
