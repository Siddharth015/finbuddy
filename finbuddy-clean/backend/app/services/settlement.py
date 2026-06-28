"""Compute net balances and a minimal set of settle-up transfers.

Only ``shared`` transactions contribute to settlement. For each shared
transaction the payer fronts the full amount and every member owes their
``split`` share. The net balance per member is::

    paid_for_others - owed_to_others

A positive balance means the member is owed money; negative means they owe.
A greedy algorithm then produces a minimal list of transfers that zeroes out
all balances.
"""
from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.models.enums import TxnScope
from app.models.transaction import Transaction

_CENT = Decimal("0.01")


def compute_balances(
    transactions: Iterable[Transaction], member_ids: Iterable[int]
) -> dict[int, Decimal]:
    """Return ``{user_id: net_balance}`` for the given members."""
    balances: dict[int, Decimal] = {uid: Decimal("0") for uid in member_ids}

    for txn in transactions:
        if txn.scope != TxnScope.SHARED:
            continue
        payer = txn.user_id
        if payer not in balances:
            balances[payer] = Decimal("0")

        # The payer is credited the full amount they fronted.
        balances[payer] += txn.amount
        # Each member is debited their share.
        for split in txn.splits:
            if split.user_id not in balances:
                balances[split.user_id] = Decimal("0")
            balances[split.user_id] -= split.share

    return {uid: bal.quantize(_CENT) for uid, bal in balances.items()}


def minimal_transfers(balances: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    """Greedily settle balances. Returns ``(from_user, to_user, amount)``."""
    creditors = sorted(
        ((uid, bal) for uid, bal in balances.items() if bal > _CENT),
        key=lambda x: x[1],
        reverse=True,
    )
    debtors = sorted(
        ((uid, -bal) for uid, bal in balances.items() if bal < -_CENT),
        key=lambda x: x[1],
        reverse=True,
    )

    transfers: list[tuple[int, int, Decimal]] = []
    i = j = 0
    creditors = [list(c) for c in creditors]  # type: ignore[assignment]
    debtors = [list(d) for d in debtors]  # type: ignore[assignment]

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        amount = min(debt, credit)
        if amount > _CENT:
            transfers.append((debtor_id, creditor_id, amount.quantize(_CENT)))
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] <= _CENT:
            i += 1
        if creditors[j][1] <= _CENT:
            j += 1

    return transfers
