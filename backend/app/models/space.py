"""Spaces (budget containers) and their members."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MemberRole, SpaceType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.investment import Investment
    from app.models.transaction import Transaction
    from app.models.user import User


class Space(Base, TimestampMixin):
    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[SpaceType] = mapped_column(
        Enum(SpaceType, native_enum=False, length=16),
        default=SpaceType.SOLO,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    invite_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False
    )

    members: Mapped[list[SpaceMember]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    accounts: Mapped[list[Account]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    investments: Mapped[list[Investment]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )


class SpaceMember(Base, TimestampMixin):
    __tablename__ = "space_members"
    __table_args__ = (
        UniqueConstraint("space_id", "user_id", name="uq_space_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, native_enum=False, length=16),
        default=MemberRole.MEMBER,
        nullable=False,
    )

    space: Mapped[Space] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")
