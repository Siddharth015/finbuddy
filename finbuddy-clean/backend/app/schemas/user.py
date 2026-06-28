"""User-facing schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    first_name: str
    username: str | None = None


class MeResponse(BaseModel):
    user: UserRead
    spaces: list[SpaceRead]


from app.schemas.space import SpaceRead  # noqa: E402  (resolve forward ref)

MeResponse.model_rebuild()
