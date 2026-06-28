"""REST API routers for the Telegram Mini App."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import accounts, insights, investments, spaces, transactions, users

api_router = APIRouter(prefix="/api")
api_router.include_router(users.router)
api_router.include_router(spaces.router)
api_router.include_router(transactions.router)
api_router.include_router(accounts.router)
api_router.include_router(investments.router)
api_router.include_router(insights.router)

__all__ = ["api_router"]
