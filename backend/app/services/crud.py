"""Database operations shared by the REST API and the Telegram bot."""
from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.account import Account
from app.models.enums import MemberRole, SpaceType, TxnScope, TxnType
from app.models.space import Space, SpaceMember
from app.models.transaction import Transaction, TransactionSplit
from app.models.user import User
from app.services import categorizer
from app.services.parser import ParsedExpense, parse_expense

_INVITE_ALPHABET = string.ascii_uppercase + string.digits


def _new_invite_code(length: int = 8) -> str:
    return "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(length))


# --------------------------------------------------------------------------- #
# Users & spaces
# --------------------------------------------------------------------------- #
async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    first_name: str,
    username: str | None = None,
    language_code: str | None = None,
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )
        session.add(user)
        await session.flush()
    else:
        # Keep profile fresh.
        user.first_name = first_name
        user.username = username
        if language_code:
            user.language_code = language_code
    return user


async def create_space(
    session: AsyncSession,
    *,
    owner: User,
    name: str,
    space_type: SpaceType = SpaceType.SOLO,
    currency: str | None = None,
) -> Space:
    space = Space(
        name=name,
        type=space_type,
        currency=(currency or settings.default_currency).upper(),
        invite_code=_new_invite_code(),
    )
    space.members.append(SpaceMember(user=owner, role=MemberRole.OWNER))
    session.add(space)
    await session.flush()
    return space


async def ensure_personal_space(session: AsyncSession, user: User) -> Space:
    """Return the user's first space, creating a solo one if none exist."""
    result = await session.execute(
        select(Space)
        .join(SpaceMember)
        .where(SpaceMember.user_id == user.id)
        .order_by(Space.id)
        .options(selectinload(Space.members).selectinload(SpaceMember.user))
    )
    space = result.scalars().first()
    if space is not None:
        return space
    space = await create_space(
        session, owner=user, name=f"{user.first_name}'s Budget", space_type=SpaceType.SOLO
    )
    return await get_space(session, space.id)  # type: ignore[return-value]


async def get_space(session: AsyncSession, space_id: int) -> Space | None:
    result = await session.execute(
        select(Space)
        .where(Space.id == space_id)
        .options(selectinload(Space.members).selectinload(SpaceMember.user))
    )
    return result.scalar_one_or_none()


async def get_space_by_invite(session: AsyncSession, invite_code: str) -> Space | None:
    result = await session.execute(
        select(Space)
        .where(Space.invite_code == invite_code.upper())
        .options(selectinload(Space.members).selectinload(SpaceMember.user))
    )
    return result.scalar_one_or_none()


async def list_user_spaces(session: AsyncSession, user_id: int) -> list[Space]:
    result = await session.execute(
        select(Space)
        .join(SpaceMember)
        .where(SpaceMember.user_id == user_id)
        .order_by(Space.id)
        .options(selectinload(Space.members).selectinload(SpaceMember.user))
    )
    return list(result.scalars().unique().all())


async def join_space(
    session: AsyncSession, *, space: Space, user: User
) -> SpaceMember:
    for member in space.members:
        if member.user_id == user.id:
            return member
    member = SpaceMember(user=user, role=MemberRole.MEMBER)
    # Append to the relationship so the in-memory collection stays consistent
    # (sessions use expire_on_commit=False).
    space.members.append(member)
    # A space with more than one member is, by definition, shared.
    space.type = SpaceType.SHARED
    await session.flush()
    return member


async def is_member(session: AsyncSession, *, space_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(SpaceMember.id).where(
            SpaceMember.space_id == space_id, SpaceMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
def _equal_splits(amount: Decimal, member_ids: list[int]) -> dict[int, Decimal]:
    """Split ``amount`` equally, pushing rounding remainder onto the first member."""
    n = len(member_ids)
    if n == 0:
        return {}
    base = (amount / n).quantize(Decimal("0.01"))
    shares = {uid: base for uid in member_ids}
    remainder = amount - base * n
    shares[member_ids[0]] = (shares[member_ids[0]] + remainder).quantize(Decimal("0.01"))
    return shares


async def create_transaction(
    session: AsyncSession,
    *,
    space: Space,
    payer: User,
    amount: Decimal | None = None,
    raw_text: str | None = None,
    txn_type: TxnType = TxnType.EXPENSE,
    scope: TxnScope = TxnScope.PERSONAL,
    category: str | None = None,
    note: str | None = None,
    account_id: int | None = None,
    occurred_at: datetime | None = None,
    splits: dict[int, Decimal] | None = None,
) -> Transaction:
    """Create a transaction, parsing ``raw_text`` when explicit fields are absent."""
    if amount is None:
        if not raw_text:
            raise ValueError("Either amount or raw_text is required")
        parsed: ParsedExpense = parse_expense(raw_text)
        amount = parsed.amount
        note = note or parsed.note
        txn_type = parsed.type
    if note is None and raw_text:
        note = raw_text
    category = (category or categorizer.categorize(note or "")).lower()

    txn = Transaction(
        space_id=space.id,
        user_id=payer.id,
        account_id=account_id,
        type=txn_type,
        scope=scope,
        amount=amount,
        category=category,
        note=note,
        raw_text=raw_text,
        occurred_at=occurred_at or datetime.now(UTC),
    )
    session.add(txn)

    if scope == TxnScope.SHARED:
        member_ids = [m.user_id for m in space.members]
        if splits:
            resolved = {int(k): Decimal(str(v)) for k, v in splits.items()}
        else:
            resolved = _equal_splits(amount, member_ids)
        for uid, share in resolved.items():
            txn.splits.append(TransactionSplit(user_id=uid, share=share))

    # Keep the linked account balance in sync.
    if account_id is not None:
        account = await session.get(Account, account_id)
        if account is not None and account.space_id == space.id:
            if txn_type == TxnType.INCOME:
                account.balance += amount
            elif txn_type == TxnType.EXPENSE:
                account.balance -= amount

    await session.flush()
    return txn


async def list_transactions(
    session: AsyncSession,
    *,
    space_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.space_id == space_id)
        .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(Transaction.splits))
    )
    return list(result.scalars().all())


async def get_transaction(
    session: AsyncSession, txn_id: int
) -> Transaction | None:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.id == txn_id)
        .options(selectinload(Transaction.splits))
    )
    return result.scalar_one_or_none()
