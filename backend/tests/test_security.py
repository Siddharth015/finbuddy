import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.security import InitDataError, validate_init_data

BOT_TOKEN = "123456:test-token"


def _build_init_data(user: dict, token: str = BOT_TOKEN, auth_date: int | None = None) -> str:
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "AAEEtest",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(
        secret, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(fields)


def test_valid_init_data():
    user = {"id": 42, "first_name": "Sid", "username": "sid"}
    init_data = _build_init_data(user)
    tg = validate_init_data(init_data, BOT_TOKEN)
    assert tg.id == 42
    assert tg.first_name == "Sid"
    assert tg.username == "sid"


def test_tampered_hash_rejected():
    user = {"id": 42, "first_name": "Sid"}
    init_data = _build_init_data(user) + "0"
    with pytest.raises(InitDataError):
        validate_init_data(init_data, BOT_TOKEN)


def test_wrong_token_rejected():
    user = {"id": 42, "first_name": "Sid"}
    init_data = _build_init_data(user, token="999:other")
    with pytest.raises(InitDataError):
        validate_init_data(init_data, BOT_TOKEN)


def test_expired_init_data_rejected():
    user = {"id": 42, "first_name": "Sid"}
    init_data = _build_init_data(user, auth_date=int(time.time()) - 100_000)
    with pytest.raises(InitDataError):
        validate_init_data(init_data, BOT_TOKEN, max_age_seconds=3600)


def test_missing_raises():
    with pytest.raises(InitDataError):
        validate_init_data("", BOT_TOKEN)
