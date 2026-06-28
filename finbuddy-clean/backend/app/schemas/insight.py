"""Insight & report schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CategorySlice(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class TrendPoint(BaseModel):
    period: str  # e.g. "2026-06-01" (day) or "2026-06" (month)
    amount: Decimal


class InsightResponse(BaseModel):
    month: str
    currency: str
    total_spent: Decimal
    categories: list[CategorySlice]
    daily_trend: list[TrendPoint]
    anomalies: list[str]


class MonthlyReport(BaseModel):
    month: str
    currency: str
    total_spent: Decimal
    total_income: Decimal
    net: Decimal
    summary: str
    advice: list[str]
