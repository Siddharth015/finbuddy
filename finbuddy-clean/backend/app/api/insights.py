"""Insights, settlement and AI monthly report endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import MemberSpace, SessionDep
from app.schemas.insight import InsightResponse, MonthlyReport
from app.schemas.settlement import SettlementResponse
from app.services import analytics
from app.services.ai import monthly_summary

router = APIRouter(prefix="/spaces", tags=["insights"])


@router.get("/{space_id}/insights", response_model=InsightResponse)
async def get_insights(
    space: MemberSpace,
    session: SessionDep,
    month: str | None = None,
) -> InsightResponse:
    data = await analytics.insights(session, space, month)
    return InsightResponse.model_validate(data)


@router.get("/{space_id}/settlement", response_model=SettlementResponse)
async def get_settlement(space: MemberSpace, session: SessionDep) -> SettlementResponse:
    data = await analytics.settlement(session, space)
    return SettlementResponse.model_validate(data)


@router.get("/{space_id}/report", response_model=MonthlyReport)
async def get_report(
    space: MemberSpace,
    session: SessionDep,
    month: str | None = None,
) -> MonthlyReport:
    summary = await analytics.space_summary(session, space, month)
    insight = await analytics.insights(session, space, month)
    categories = [(c.category, c.amount) for c in insight["categories"]]
    text, advice = await monthly_summary(
        month=summary["month"],
        currency=space.currency,
        total_spent=summary["total_spent"],
        total_income=summary["total_income"],
        categories=categories,
    )
    return MonthlyReport(
        month=summary["month"],
        currency=space.currency,
        total_spent=summary["total_spent"],
        total_income=summary["total_income"],
        net=summary["net"],
        summary=text,
        advice=advice,
    )
