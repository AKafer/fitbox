import uuid
from datetime import date

from pydantic import BaseModel


class Record(BaseModel):
    id: int
    date: date
    user_id: uuid.UUID
    weight: float

    model_config = {"from_attributes": True}


class RecordCreateInput(BaseModel):
    date: date
    weight: float


class RecordCreateByAdminInput(BaseModel):
    user_id: uuid.UUID
    date: date
    weight: float
