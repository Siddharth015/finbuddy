"""Space schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MemberRole, SpaceType
from app.schemas.user import UserRead


class SpaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: SpaceType = SpaceType.SOLO
    currency: str = Field(default="INR", min_length=3, max_length=3)


class SpaceJoin(BaseModel):
    invite_code: str = Field(min_length=4, max_length=16)


class SpaceMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MemberRole
    user: UserRead


class SpaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: SpaceType
    currency: str
    invite_code: str
    members: list[SpaceMemberRead] = []


class SpaceSummary(BaseModel):
    space: SpaceRead
    month: str
    total_spent: Decimal
    total_income: Decimal
    net: Decimal
    accounts_balance: Decimal
    investments_value: Decimal
    investments_invested: Decimal
    top_category: str | None = None
