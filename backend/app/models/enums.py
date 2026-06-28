"""Enumerations shared across the domain models."""
from __future__ import annotations

import enum


class SpaceType(str, enum.Enum):
    SOLO = "solo"
    SHARED = "shared"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class TxnType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class TxnScope(str, enum.Enum):
    """Who a transaction belongs to within a shared space."""

    PERSONAL = "personal"  # only the payer
    SHARED = "shared"      # split between members per `split`


class AccountType(str, enum.Enum):
    BANK = "bank"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    WALLET = "wallet"


class InvestmentType(str, enum.Enum):
    EQUITY = "equity"
    MUTUAL_FUND = "mutual_fund"
    FIXED_DEPOSIT = "fixed_deposit"
    BOND = "bond"
    CRYPTO = "crypto"
    GOLD = "gold"
    OTHER = "other"
