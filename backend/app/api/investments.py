"""Investment endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, MemberSpace, SessionDep
from app.models.investment import Investment
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentRead,
    InvestmentUpdate,
)

router = APIRouter(prefix="/spaces", tags=["investments"])


@router.get("/{space_id}/investments", response_model=list[InvestmentRead])
async def list_investments(
    space: MemberSpace, session: SessionDep
) -> list[InvestmentRead]:
    result = await session.execute(
        select(Investment).where(Investment.space_id == space.id).order_by(Investment.id)
    )
    return [InvestmentRead.model_validate(i) for i in result.scalars().all()]


@router.post(
    "/{space_id}/investments",
    response_model=InvestmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_investment(
    payload: InvestmentCreate,
    space: MemberSpace,
    session: SessionDep,
    user: CurrentUser,
) -> InvestmentRead:
    investment = Investment(
        space_id=space.id,
        user_id=user.id,
        name=payload.name,
        type=payload.type,
        units=payload.units,
        avg_buy_price=payload.avg_buy_price,
        current_price=payload.current_price,
        currency=payload.currency.upper(),
    )
    session.add(investment)
    await session.commit()
    await session.refresh(investment)
    return InvestmentRead.model_validate(investment)


@router.patch("/{space_id}/investments/{investment_id}", response_model=InvestmentRead)
async def update_investment(
    investment_id: int,
    payload: InvestmentUpdate,
    space: MemberSpace,
    session: SessionDep,
) -> InvestmentRead:
    investment = await session.get(Investment, investment_id)
    if investment is None or investment.space_id != space.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(investment, field, value)
    await session.commit()
    await session.refresh(investment)
    return InvestmentRead.model_validate(investment)


@router.delete(
    "/{space_id}/investments/{investment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_investment(
    investment_id: int,
    space: MemberSpace,
    session: SessionDep,
) -> Response:
    investment = await session.get(Investment, investment_id)
    if investment is None or investment.space_id != space.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )
    await session.delete(investment)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
