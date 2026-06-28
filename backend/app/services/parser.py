"""Parse natural shorthand expense messages like ``1000-zomato``.

Supported shapes (case-insensitive, flexible whitespace)::

    1000-zomato            -> expense 1000, note "zomato"
    1000 zomato            -> expense 1000, note "zomato"
    -250 auto              -> expense 250, note "auto"
    +50000 salary          -> income 50000, note "salary"
    1.2k groceries         -> expense 1200, note "groceries"
    rent 15000             -> expense 15000, note "rent"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.models.enums import TxnType

# Matches an amount with optional sign and optional k/m/l(akh)/cr suffix.
_AMOUNT_RE = re.compile(
    r"(?P<sign>[+-])?\s*(?P<num>\d+(?:[.,]\d+)?)\s*(?P<suffix>k|m|l|lakh|cr)?",
    re.IGNORECASE,
)

_SUFFIX_MULTIPLIER = {
    "k": Decimal("1000"),
    "m": Decimal("1000000"),
    "l": Decimal("100000"),
    "lakh": Decimal("100000"),
    "cr": Decimal("10000000"),
}

_INCOME_HINTS = {
    "salary",
    "income",
    "credited",
    "refund",
    "cashback",
    "interest",
    "dividend",
    "bonus",
}


@dataclass(frozen=True)
class ParsedExpense:
    amount: Decimal
    note: str
    type: TxnType


class ParseError(ValueError):
    """Raised when a message cannot be interpreted as an expense."""


def parse_expense(text: str) -> ParsedExpense:
    """Parse a shorthand message into an amount, note and transaction type.

    Raises :class:`ParseError` when no amount can be found.
    """
    if not text or not text.strip():
        raise ParseError("Empty message")

    raw = text.strip()
    match = _AMOUNT_RE.search(raw)
    if not match:
        raise ParseError("Could not find an amount in the message")

    num = match.group("num").replace(",", "")
    try:
        amount = Decimal(num)
    except InvalidOperation as exc:  # pragma: no cover - guarded by regex
        raise ParseError("Invalid amount") from exc

    suffix = (match.group("suffix") or "").lower()
    if suffix:
        amount *= _SUFFIX_MULTIPLIER[suffix]
    amount = amount.quantize(Decimal("0.01"))

    if amount <= 0:
        raise ParseError("Amount must be greater than zero")

    # Note = everything except the matched amount token.
    note = (raw[: match.start()] + " " + raw[match.end():]).strip()
    note = re.sub(r"^[\s\-:]+|[\s\-:]+$", "", note)
    note = re.sub(r"\s{2,}", " ", note)

    sign = match.group("sign")
    note_lower = note.lower()
    is_income = sign == "+" or any(hint in note_lower for hint in _INCOME_HINTS)
    txn_type = TxnType.INCOME if is_income else TxnType.EXPENSE

    return ParsedExpense(amount=amount, note=note or "expense", type=txn_type)
