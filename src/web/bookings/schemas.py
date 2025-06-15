import uuid
from datetime import datetime

from pydantic import BaseModel


class Booking(BaseModel):
    id: int
    created_at: datetime
    source_record: str | None = None
    user_id: uuid.UUID
    slot_id: int

    class Config:
        orm_mode = True


class BookingCreateInput(BaseModel):
    created_at: datetime
    slot_id: int
    source_record: str | None = None
