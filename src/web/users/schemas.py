import uuid
from datetime import datetime, date, time

from fastapi_users import schemas
from pydantic import EmailStr, Field, BaseModel, Extra


class Transaction(BaseModel):
    id: int
    created_at: datetime
    count: int
    payment_method: str | None = None
    money_amount: float | None = 0.0

    model_config = {"from_attributes": True}


class Slot(BaseModel):
    id: int
    type: str | None
    time: datetime
    is_done: bool = False

    model_config = {"from_attributes": True}


class Booking(BaseModel):
    id: int
    created_at: datetime
    source_record: str | None = None
    slot_id: int
    power: float | None = None
    energy: float | None = None
    tempo: float | None = None
    slot: Slot | None = None

    model_config = {"from_attributes": True}


class Record(BaseModel):
    id: int
    date: date
    weight: float

    model_config = {"from_attributes": True}


class UserRead(schemas.BaseUser[uuid.UUID]):
    email: EmailStr
    name: str
    last_name: str
    father_name: str | None
    phone: str | None
    telegram_id: str | None
    photo_url: str | None
    gender: str | None
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime | None
    age: int | None = 0
    energy: float | None = 0
    status: str | None = None
    score: int | None = 0
    count_trainings: int | None = 0
    bookings: list[Booking] | None = []
    records: list[Record] | None = []
    transactions: list[Transaction] | None = []

    is_active: bool = Field(True, exclude=True)
    is_verified: bool = Field(False, exclude=True)
    is_superuser: bool = Field(False, exclude=True)


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str
    name: str
    last_name: str
    father_name: str | None = None
    phone: str | None = None
    telegram_id: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    is_active: bool = Field(True, exclude=True)
    is_verified: bool = Field(False, exclude=True)
    is_superuser: bool = Field(False, exclude=True)


class UserUpdate(schemas.BaseUserUpdate):
    email: EmailStr | None = None
    password: str | None = None
    name: str | None = None
    last_name: str | None = None
    father_name: str | None = None
    phone: str | None = None
    telegram_id: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    is_active: bool = Field(True, exclude=True)
    is_verified: bool = Field(False, exclude=True)
    is_superuser: bool = Field(False, exclude=True)


class UserListRead(schemas.BaseUser[uuid.UUID]):
    email: EmailStr
    name: str
    last_name: str
    father_name: str | None
    phone: str | None
    telegram_id: str | None
    gender: str | None = None
    date_of_birth: date | None
    age: int | None = 0
    energy: float | None = 0
    status: str | None = None
    score: int | None = 0
    count_trainings: int | None = 0
    is_active: bool = Field(True, exclude=True)
    is_verified: bool = Field(False, exclude=True)
    is_superuser: bool = Field(False, exclude=True)
