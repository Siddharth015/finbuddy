"""Account schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: AccountType = AccountType.BANK
    balance: Decimal = Decimal("0")
    currency: str = Field(default="INR", min_length=3, max_length=3)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    type: AccountType | None = None
    balance: Decimal | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: AccountType
    balance: Decimal
    currency: str
    user_id: int
