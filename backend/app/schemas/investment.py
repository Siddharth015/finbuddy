"""Investment schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import InvestmentType


class InvestmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: InvestmentType = InvestmentType.EQUITY
    units: Decimal = Field(default=Decimal("0"), ge=0)
    avg_buy_price: Decimal = Field(default=Decimal("0"), ge=0)
    current_price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)


class InvestmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    units: Decimal | None = Field(default=None, ge=0)
    avg_buy_price: Decimal | None = Field(default=None, ge=0)
    current_price: Decimal | None = Field(default=None, ge=0)


class InvestmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: InvestmentType
    units: Decimal
    avg_buy_price: Decimal
    current_price: Decimal
    currency: str
    user_id: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def invested(self) -> Decimal:
        return (self.units * self.avg_buy_price).quantize(Decimal("0.01"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_value(self) -> Decimal:
        return (self.units * self.current_price).quantize(Decimal("0.01"))
