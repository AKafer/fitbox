import uuid
from datetime import datetime

from pydantic import BaseModel


class Booking(BaseModel):
    id: int
    created_at: datetime
    source_record: str | None = None
    user_id: uuid.UUID

    class Config:
        orm_mode = True


class Slot(BaseModel):
    id: int
    type: str | None
    time: datetime
    number_of_places: int
    free_places: int | None = 0
    bookings: list[Booking]
    bindings: dict[str, str] | None = None

    model_config = {"from_attributes": True}


class SlotCreateInput(BaseModel):
    type: str | None = None
    time: datetime
    number_of_places: int


class BulkSlotCreateInput(BaseModel):
    slots: list[SlotCreateInput]


class SlotUpdateInput(BaseModel):
    type: str | None = None
    time: datetime | None = None
    number_of_places: int | None = None
    bindings: dict[str, str] | None = None


class Binding(BaseModel):
    user_id: uuid.UUID
    sensor_id: str


class BindInput(BaseModel):
    slot_id: int
    bindings: list[Binding]
