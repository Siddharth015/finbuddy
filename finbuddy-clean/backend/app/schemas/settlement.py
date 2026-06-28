"""Settlement ("who owes whom") schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.schemas.user import UserRead


class SettlementEntry(BaseModel):
    from_user: UserRead
    to_user: UserRead
    amount: Decimal


class SettlementResponse(BaseModel):
    currency: str
    # Net balance per user id: positive = is owed money, negative = owes.
    balances: dict[int, Decimal]
    transfers: list[SettlementEntry]
