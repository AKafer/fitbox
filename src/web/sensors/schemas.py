from typing import List

from pydantic import BaseModel


class Hit(BaseModel):
    timeMs: int
    maxAccel: float


class HitsChunk(BaseModel):
    device_id: str
    session_id: str
    sprint_id: str | None = None
    hits: List[Hit]


class StartSprintInptut(BaseModel):
    session_id: int
    blink_interval: int
    led_on_ms: int