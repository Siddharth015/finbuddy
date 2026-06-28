"""Aggregations that power the dashboard, insights and reports."""
from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.enums import TxnScope, TxnType
from app.models.investment import Investment
from app.models.space import Space
from app.models.transaction import Transaction
from app.schemas.insight import CategorySlice, TrendPoint
from app.services import settlement as settle

_CENT = Decimal("0.01")


def month_bounds(month: str | None) -> tuple[datetime, datetime, str]:
    """Return ``(start, end_exclusive, label)`` for ``YYYY-MM`` (default: now)."""
    if month:
        year, mon = (int(p) for p in month.split("-"))
    else:
        today = datetime.now(UTC)
        year, mon = today.year, today.month
    start = datetime(year, mon, 1, tzinfo=UTC)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=UTC)
    return start, end, f"{year:04d}-{mon:02d}"


async def _totals(
    session: AsyncSession, space_id: int, start: datetime, end: datetime
) -> tuple[Decimal, Decimal]:
    result = await session.execute(
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.space_id == space_id,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.type)
    )
    spent = Decimal("0")
    income = Decimal("0")
    for txn_type, total in result.all():
        total = Decimal(total)
        if txn_type == TxnType.EXPENSE:
            spent += total
        elif txn_type == TxnType.INCOME:
            income += total
    return spent.quantize(_CENT), income.quantize(_CENT)


async def _category_breakdown(
    session: AsyncSession, space_id: int, start: datetime, end: datetime
) -> list[tuple[str, Decimal]]:
    result = await session.execute(
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.space_id == space_id,
            Transaction.type == TxnType.EXPENSE,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    return [(cat, Decimal(total).quantize(_CENT)) for cat, total in result.all()]


async def space_summary(
    session: AsyncSession, space: Space, month: str | None = None
) -> dict:
    start, end, label = month_bounds(month)
    spent, income = await _totals(session, space.id, start, end)
    categories = await _category_breakdown(session, space.id, start, end)

    acc_total = await session.scalar(
        select(func.coalesce(func.sum(Account.balance), 0)).where(
            Account.space_id == space.id
        )
    )
    investments = await session.scalars(
        select(Investment).where(Investment.space_id == space.id)
    )
    inv_value = Decimal("0")
    inv_invested = Decimal("0")
    for inv in investments:
        inv_value += inv.current_value
        inv_invested += inv.invested

    return {
        "space": space,
        "month": label,
        "total_spent": spent,
        "total_income": income,
        "net": (income - spent).quantize(_CENT),
        "accounts_balance": Decimal(acc_total or 0).quantize(_CENT),
        "investments_value": inv_value.quantize(_CENT),
        "investments_invested": inv_invested.quantize(_CENT),
        "top_category": categories[0][0] if categories else None,
    }


async def insights(
    session: AsyncSession, space: Space, month: str | None = None
) -> dict:
    start, end, label = month_bounds(month)
    spent, _ = await _totals(session, space.id, start, end)
    raw_categories = await _category_breakdown(session, space.id, start, end)

    categories = [
        CategorySlice(
            category=cat,
            amount=amt,
            percentage=float((amt / spent * 100).quantize(Decimal("0.1")))
            if spent > 0
            else 0.0,
        )
        for cat, amt in raw_categories
    ]

    # Daily trend.
    result = await session.execute(
        select(Transaction.occurred_at, Transaction.amount).where(
            Transaction.space_id == space.id,
            Transaction.type == TxnType.EXPENSE,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
    )
    by_day: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    for occurred_at, amount in result.all():
        by_day[occurred_at.date()] += Decimal(amount)
    daily_trend = [
        TrendPoint(period=d.isoformat(), amount=amt.quantize(_CENT))
        for d, amt in sorted(by_day.items())
    ]

    anomalies = _detect_anomalies(by_day, raw_categories, spent)

    return {
        "month": label,
        "currency": space.currency,
        "total_spent": spent,
        "categories": categories,
        "daily_trend": daily_trend,
        "anomalies": anomalies,
    }


def _detect_anomalies(
    by_day: dict[date, Decimal],
    categories: list[tuple[str, Decimal]],
    total: Decimal,
) -> list[str]:
    anomalies: list[str] = []
    if by_day:
        values = list(by_day.values())
        avg = sum(values, Decimal("0")) / len(values)
        peak_day, peak_amt = max(by_day.items(), key=lambda x: x[1])
        if avg > 0 and peak_amt > avg * 2:
            anomalies.append(
                f"Spending on {peak_day.isoformat()} ({peak_amt}) was more than "
                "double your daily average."
            )
    if categories and total > 0:
        top_cat, top_amt = categories[0]
        share = top_amt / total * 100
        if share > 50:
            anomalies.append(
                f"'{top_cat}' accounts for {share:.0f}% of spending this month."
            )
    return anomalies


async def settlement(session: AsyncSession, space: Space) -> dict:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.space_id == space.id, Transaction.scope == TxnScope.SHARED)
        .options(selectinload(Transaction.splits))
    )
    transactions = list(result.scalars().all())
    member_ids = [m.user_id for m in space.members]
    balances = settle.compute_balances(transactions, member_ids)
    transfers = settle.minimal_transfers(balances)

    members_by_id = {m.user_id: m.user for m in space.members}
    return {
        "currency": space.currency,
        "balances": balances,
        "transfers": [
            {
                "from_user": members_by_id[frm],
                "to_user": members_by_id[to],
                "amount": amt,
            }
            for frm, to, amt in transfers
            if frm in members_by_id and to in members_by_id
        ],
    }
