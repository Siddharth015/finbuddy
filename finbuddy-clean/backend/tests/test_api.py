"""End-to-end API tests against an in-memory SQLite database.

These exercise the real request flow: Telegram initData auth, space creation,
transaction logging (with shorthand parsing) and the dashboard summary.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.deps import get_session
from app.main import app
from app.models import Base

BOT_TOKEN = settings.bot_token


def make_init_data(user_id: int, first_name: str = "Tester") -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(
            {"id": user_id, "first_name": first_name}, separators=(",", ":")
        ),
    }
    dcs = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


def auth(user_id: int) -> dict[str, str]:
    return {"X-Telegram-Init-Data": make_init_data(user_id)}


@pytest.mark.asyncio
async def test_me_creates_personal_space(client):
    res = await client.get("/api/me", headers=auth(1001))
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["telegram_id"] == 1001
    assert len(body["spaces"]) == 1
    assert body["spaces"][0]["type"] == "solo"


@pytest.mark.asyncio
async def test_unauthenticated_is_rejected(client):
    res = await client.get("/api/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_log_expense_and_summary(client):
    me = (await client.get("/api/me", headers=auth(2002))).json()
    space_id = me["spaces"][0]["id"]

    # Log an expense via shorthand.
    res = await client.post(
        f"/api/spaces/{space_id}/transactions",
        headers=auth(2002),
        json={"raw_text": "1200-zomato"},
    )
    assert res.status_code == 201
    txn = res.json()
    assert txn["amount"] == "1200.00"
    assert txn["category"] == "food"
    assert txn["type"] == "expense"

    # Log income.
    await client.post(
        f"/api/spaces/{space_id}/transactions",
        headers=auth(2002),
        json={"raw_text": "+50000 salary"},
    )

    summary = (
        await client.get(f"/api/spaces/{space_id}/summary", headers=auth(2002))
    ).json()
    assert summary["total_spent"] == "1200.00"
    assert summary["total_income"] == "50000.00"
    assert summary["net"] == "48800.00"
    assert summary["top_category"] == "food"


@pytest.mark.asyncio
async def test_shared_space_join_and_settlement(client):
    # User A creates a shared space.
    space = (
        await client.post(
            "/api/spaces",
            headers=auth(3003),
            json={"name": "Home", "type": "shared", "currency": "INR"},
        )
    ).json()
    space_id = space["id"]
    invite = space["invite_code"]

    # User B joins it.
    joined = (
        await client.post(
            "/api/spaces/join",
            headers=auth(4004),
            json={"invite_code": invite},
        )
    ).json()
    assert len(joined["members"]) == 2

    # User A pays a shared expense split equally.
    await client.post(
        f"/api/spaces/{space_id}/transactions",
        headers=auth(3003),
        json={"raw_text": "1000 dinner", "scope": "shared"},
    )

    settlement = (
        await client.get(f"/api/spaces/{space_id}/settlement", headers=auth(4004))
    ).json()
    # B owes A 500.
    assert len(settlement["transfers"]) == 1
    assert settlement["transfers"][0]["amount"] == "500.00"


@pytest.mark.asyncio
async def test_account_crud(client):
    me = (await client.get("/api/me", headers=auth(5005))).json()
    space_id = me["spaces"][0]["id"]

    created = (
        await client.post(
            f"/api/spaces/{space_id}/accounts",
            headers=auth(5005),
            json={"name": "HDFC", "type": "bank", "balance": "10000"},
        )
    ).json()
    assert created["name"] == "HDFC"

    accounts = (
        await client.get(f"/api/spaces/{space_id}/accounts", headers=auth(5005))
    ).json()
    assert len(accounts) == 1

    res = await client.delete(
        f"/api/spaces/{space_id}/accounts/{created['id']}", headers=auth(5005)
    )
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_non_member_cannot_access_space(client):
    space = (
        await client.post(
            "/api/spaces",
            headers=auth(6006),
            json={"name": "Private", "type": "solo", "currency": "INR"},
        )
    ).json()
    res = await client.get(
        f"/api/spaces/{space['id']}/summary", headers=auth(7007)
    )
    assert res.status_code == 403
