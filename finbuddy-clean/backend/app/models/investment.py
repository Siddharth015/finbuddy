"""Investment holdings tracked inside a space."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import InvestmentType

if TYPE_CHECKING:
    from app.models.space import Space
    from app.models.user import User


class Investment(Base, TimestampMixin):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[InvestmentType] = mapped_column(
        Enum(InvestmentType, native_enum=False, length=16),
        default=InvestmentType.EQUITY,
        nullable=False,
    )
    units: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), default=Decimal("0"), nullable=False
    )
    avg_buy_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    current_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    space: Mapped[Space] = relationship(back_populates="investments")
    owner: Mapped[User] = relationship()

    @property
    def invested(self) -> Decimal:
        return (self.units * self.avg_buy_price).quantize(Decimal("0.01"))

    @property
    def current_value(self) -> Decimal:
        return (self.units * self.current_price).quantize(Decimal("0.01"))
