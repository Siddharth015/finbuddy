"""Account endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import CurrentUser, MemberSpace, SessionDep
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/spaces", tags=["accounts"])


@router.get("/{space_id}/accounts", response_model=list[AccountRead])
async def list_accounts(space: MemberSpace, session: SessionDep) -> list[AccountRead]:
    result = await session.execute(
        select(Account).where(Account.space_id == space.id).order_by(Account.id)
    )
    return [AccountRead.model_validate(a) for a in result.scalars().all()]


@router.post(
    "/{space_id}/accounts",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    payload: AccountCreate,
    space: MemberSpace,
    session: SessionDep,
    user: CurrentUser,
) -> AccountRead:
    account = Account(
        space_id=space.id,
        user_id=user.id,
        name=payload.name,
        type=payload.type,
        balance=payload.balance,
        currency=payload.currency.upper(),
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return AccountRead.model_validate(account)


@router.patch("/{space_id}/accounts/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    space: MemberSpace,
    session: SessionDep,
) -> AccountRead:
    account = await session.get(Account, account_id)
    if account is None or account.space_id != space.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(account, field, value)
    await session.commit()
    await session.refresh(account)
    return AccountRead.model_validate(account)


@router.delete(
    "/{space_id}/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_account(
    account_id: int,
    space: MemberSpace,
    session: SessionDep,
) -> Response:
    account = await session.get(Account, account_id)
    if account is None or account.space_id != space.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    await session.delete(account)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
