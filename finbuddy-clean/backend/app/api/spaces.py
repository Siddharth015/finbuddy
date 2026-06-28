"""Space management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, MemberSpace, SessionDep
from app.schemas.space import (
    SpaceCreate,
    SpaceJoin,
    SpaceRead,
    SpaceSummary,
)
from app.services import analytics, crud

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get("", response_model=list[SpaceRead])
async def list_spaces(session: SessionDep, user: CurrentUser) -> list[SpaceRead]:
    spaces = await crud.list_user_spaces(session, user.id)
    return [SpaceRead.model_validate(s) for s in spaces]


@router.post("", response_model=SpaceRead, status_code=status.HTTP_201_CREATED)
async def create_space(
    payload: SpaceCreate, session: SessionDep, user: CurrentUser
) -> SpaceRead:
    space = await crud.create_space(
        session,
        owner=user,
        name=payload.name,
        space_type=payload.type,
        currency=payload.currency,
    )
    await session.commit()
    loaded = await crud.get_space(session, space.id)
    return SpaceRead.model_validate(loaded)


@router.post("/join", response_model=SpaceRead)
async def join_space(
    payload: SpaceJoin, session: SessionDep, user: CurrentUser
) -> SpaceRead:
    space = await crud.get_space_by_invite(session, payload.invite_code)
    if space is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code"
        )
    await crud.join_space(session, space=space, user=user)
    await session.commit()
    loaded = await crud.get_space(session, space.id)
    return SpaceRead.model_validate(loaded)


@router.get("/{space_id}", response_model=SpaceRead)
async def get_space(space: MemberSpace) -> SpaceRead:
    return SpaceRead.model_validate(space)


@router.get("/{space_id}/summary", response_model=SpaceSummary)
async def get_summary(
    space: MemberSpace,
    session: SessionDep,
    month: str | None = None,
) -> SpaceSummary:
    data = await analytics.space_summary(session, space, month)
    return SpaceSummary.model_validate(data)
