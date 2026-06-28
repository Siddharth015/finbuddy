"""Transactions and their per-member splits."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import TxnScope, TxnType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.space import Space
    from app.models.user import User


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[TxnType] = mapped_column(
        Enum(TxnType, native_enum=False, length=16),
        default=TxnType.EXPENSE,
        nullable=False,
    )
    scope: Mapped[TxnScope] = mapped_column(
        Enum(TxnScope, native_enum=False, length=16),
        default=TxnScope.PERSONAL,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(48), default="other", nullable=False)
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(String(256), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    space: Mapped[Space] = relationship(back_populates="transactions")
    payer: Mapped[User] = relationship()
    account: Mapped[Account | None] = relationship()
    splits: Mapped[list[TransactionSplit]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    share: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    transaction: Mapped[Transaction] = relationship(back_populates="splits")
    user: Mapped[User] = relationship()
