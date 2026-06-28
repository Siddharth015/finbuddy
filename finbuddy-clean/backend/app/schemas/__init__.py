"""Pydantic schemas (request/response models) for the REST API."""
from __future__ import annotations

from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.schemas.common import Message
from app.schemas.insight import CategorySlice, InsightResponse, MonthlyReport, TrendPoint
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentRead,
    InvestmentUpdate,
)
from app.schemas.settlement import SettlementEntry, SettlementResponse
from app.schemas.space import (
    SpaceCreate,
    SpaceJoin,
    SpaceMemberRead,
    SpaceRead,
    SpaceSummary,
)
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionSplitRead,
)
from app.schemas.user import MeResponse, UserRead

__all__ = [
    "Message",
    "UserRead",
    "MeResponse",
    "SpaceCreate",
    "SpaceJoin",
    "SpaceRead",
    "SpaceMemberRead",
    "SpaceSummary",
    "AccountCreate",
    "AccountUpdate",
    "AccountRead",
    "TransactionCreate",
    "TransactionRead",
    "TransactionSplitRead",
    "InvestmentCreate",
    "InvestmentUpdate",
    "InvestmentRead",
    "SettlementEntry",
    "SettlementResponse",
    "CategorySlice",
    "TrendPoint",
    "InsightResponse",
    "MonthlyReport",
]
