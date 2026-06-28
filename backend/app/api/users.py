"""Current-user endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.schemas.user import MeResponse
from app.services import crud

router = APIRouter(tags=["users"])


@router.get("/me", response_model=MeResponse)
async def read_me(session: SessionDep, user: CurrentUser) -> MeResponse:
    spaces = await crud.list_user_spaces(session, user.id)
    if not spaces:
        await crud.ensure_personal_space(session, user)
        await session.commit()
        spaces = await crud.list_user_spaces(session, user.id)
    return MeResponse.model_validate({"user": user, "spaces": spaces})
