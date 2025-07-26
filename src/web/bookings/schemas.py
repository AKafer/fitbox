import uuid
from datetime import datetime

from pydantic import BaseModel


class Slot(BaseModel):
    id: int
    type: str | None
    time: datetime
    number_of_places: int
    free_places: int | None = 0

    model_config = {"from_attributes": True}



class Booking(BaseModel):
    id: int
    created_at: datetime
    source_record: str | None = None
    user_id: uuid.UUID
    slot_id: int
    is_done: bool = False
    power: float | None = None
    energy: float | None = None
    tempo: float | None = None
    slot: Slot | None = None
    sensor_id: str | None = None


    model_config = {"from_attributes": True}


class DetailedBooking(Booking):
    sprints_data: dict | None = None

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


class BookingUpdateInput(BaseModel):
    is_done: bool | None = None
