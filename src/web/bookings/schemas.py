import uuid
from datetime import datetime

from pydantic import BaseModel


class Booking(BaseModel):
    id: int
    created_at: datetime
    source_record: str | None = None
    user_id: uuid.UUID
    slot_id: int

    model_config = {"from_attributes": True}


class BookingCreateInput(BaseModel):
    created_at: datetime
    slot_id: int
    source_record: str | None = None


class BookingCreateByAdminInput(BaseModel):
    user_id: uuid.UUID
    created_at: datetime
    slot_id: int
    source_record: str | None = None
