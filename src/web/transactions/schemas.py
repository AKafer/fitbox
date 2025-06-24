import uuid
from datetime import datetime

from pydantic import BaseModel


class Transaction(BaseModel):
    id: int
    created_at: datetime
    user_id: uuid.UUID
    count: int
    payment_method: str | None = None
    money_amount: float | None = 0.0

    model_config = {"from_attributes": True}


class TransactionCreateInput(BaseModel):
    created_at: datetime
    count: int
    payment_method: str | None = None
    money_amount: float | None = 0.0


class TransactionCreateByAdminInput(BaseModel):
    created_at: datetime
    user_id: uuid.UUID
    count: int
    payment_method: str | None = None
    money_amount: float | None = 0.0
