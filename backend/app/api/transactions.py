"""Transaction endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.deps import CurrentUser, MemberSpace, SessionDep
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.services import crud
from app.services.parser import ParseError

router = APIRouter(prefix="/spaces", tags=["transactions"])


@router.get("/{space_id}/transactions", response_model=list[TransactionRead])
async def list_transactions(
    space: MemberSpace,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[TransactionRead]:
    txns = await crud.list_transactions(
        session, space_id=space.id, limit=limit, offset=offset
    )
    return [TransactionRead.model_validate(t) for t in txns]


@router.post(
    "/{space_id}/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    payload: TransactionCreate,
    space: MemberSpace,
    session: SessionDep,
    user: CurrentUser,
) -> TransactionRead:
    try:
        txn = await crud.create_transaction(
            session,
            space=space,
            payer=user,
            amount=payload.amount,
            raw_text=payload.raw_text,
            txn_type=payload.type,
            scope=payload.scope,
            category=payload.category,
            note=payload.note,
            account_id=payload.account_id,
            occurred_at=payload.occurred_at,
            splits=payload.splits,
        )
    except (ParseError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await session.commit()
    loaded = await crud.get_transaction(session, txn.id)
    return TransactionRead.model_validate(loaded)


@router.delete(
    "/{space_id}/transactions/{txn_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_transaction(
    txn_id: int,
    space: MemberSpace,
    session: SessionDep,
) -> Response:
    txn = await crud.get_transaction(session, txn_id)
    if txn is None or txn.space_id != space.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    await session.delete(txn)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
