from typing import List

from pydantic import BaseModel, Field, ConfigDict


class RegisterInput(BaseModel):
    device_id: str
    ip: str


class Hit(BaseModel):
    timeMs: int
    maxAccel: float


class HitsChunk(BaseModel):
    device_id: str
    session_id: str
    sprint_id: str | None = None
    blink_interval: str | None = None
    hits: List[Hit]
    is_last: bool = False
    force_threshold: float | None = None
    trim_percent: float | None = None
    percentile_level: float | None = None


class StartSprintInptut(BaseModel):
    session_id: int
    sprint_id: int
    blink_interval: int
    led_on_ms: int