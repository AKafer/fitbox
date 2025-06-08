from datetime import datetime

from pydantic import BaseModel


class Slot(BaseModel):
    id: int
    type: str | None
    time: datetime
    number_of_places: int
    free_places: int | None = 0

    class Config:
        orm_mode = True


class SlotCreateInput(BaseModel):
    type: str | None = None
    time: datetime
    number_of_places: int


class SlotUpdateInput(BaseModel):
    type: str | None = None
    time: datetime | None = None
    number_of_places: int | None = None
