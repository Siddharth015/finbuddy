"""FastAPI dependencies: DB session, current user, and space access guards."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.space import Space
from app.models.user import User
from app.security import InitDataError, validate_init_data
from app.services import crud

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
) -> User:
    """Resolve the caller from a Telegram Mini App ``initData`` payload.

    Accepts the data either in the ``X-Telegram-Init-Data`` header or as an
    ``Authorization: tma <initData>`` bearer-style header.
    """
    init_data = x_telegram_init_data
    if not init_data and authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() in {"tma", "twa", "bearer"} and value:
            init_data = value

    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Telegram init data",
        )

    try:
        tg_user = validate_init_data(init_data, settings.bot_token)
    except InitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    user = await crud.get_or_create_user(
        session,
        telegram_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        language_code=tg_user.language_code,
    )
    await session.commit()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_member_space(
    space_id: Annotated[int, Path()],
    session: SessionDep,
    user: CurrentUser,
) -> Space:
    """Load a space and ensure the current user is a member of it."""
    space = await crud.get_space(session, space_id)
    if space is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )
    if not any(m.user_id == user.id for m in space.members):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this space",
        )
    return space


MemberSpace = Annotated[Space, Depends(get_member_space)]
