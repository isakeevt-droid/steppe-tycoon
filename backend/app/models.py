from __future__ import annotations

from pydantic import BaseModel

class BuyRequest(BaseModel):
    id: str


class SwipeRequest(BaseModel):
    direction: str


class HoldRequest(BaseModel):
    duration_ms: int


class PlayerIdentity(BaseModel):
    player_id: str
    display_name: str
    username: str | None = None
    is_telegram: bool = False
