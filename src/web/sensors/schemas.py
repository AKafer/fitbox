from typing import List

from pydantic import BaseModel


class Hit(BaseModel):
    timeMs: int
    maxAccel: float

class HitsChunk(BaseModel):
    device_id: str
    session_id: str
    hits: List[Hit]