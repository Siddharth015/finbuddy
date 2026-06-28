"""Transaction schemas."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TxnScope, TxnType


class TransactionSplitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    share: Decimal


class TransactionCreate(BaseModel):
    # Either provide a raw shorthand string (parsed server-side) ...
    raw_text: str | None = Field(default=None, max_length=256)
    # ... or explicit fields.
    amount: Decimal | None = Field(default=None, gt=0)
    type: TxnType = TxnType.EXPENSE
    scope: TxnScope = TxnScope.PERSONAL
    category: str | None = Field(default=None, max_length=48)
    note: str | None = Field(default=None, max_length=256)
    account_id: int | None = None
    occurred_at: datetime | None = None
    # Map of user_id -> share amount for custom shared splits.
    splits: dict[int, Decimal] | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    user_id: int
    account_id: int | None
    type: TxnType
    scope: TxnScope
    amount: Decimal
    category: str
    note: str | None
    raw_text: str | None
    occurred_at: datetime
    splits: list[TransactionSplitRead] = []
