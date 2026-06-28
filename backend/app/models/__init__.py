"""ORM models package.

Importing every model here guarantees they are registered on the shared
``Base.metadata`` before Alembic autogenerate or ``create_all`` run.
"""
from __future__ import annotations

from app.models.account import Account
from app.models.base import Base, TimestampMixin
from app.models.investment import Investment
from app.models.space import Space, SpaceMember
from app.models.transaction import Transaction, TransactionSplit
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Space",
    "SpaceMember",
    "Account",
    "Transaction",
    "TransactionSplit",
    "Investment",
]
