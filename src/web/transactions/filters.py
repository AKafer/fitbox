from datetime import datetime

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from database.models import Transactions


class TransactionsFilter(Filter):
    user_id__in: list[str] | None = Field(default=None)
    count__gt: int | None = Field(default=None)
    count__lt: int | None = Field(default=None)
    time__gt: datetime | None = Field(default=None)
    time__lt: datetime | None = Field(default=None)

    class Constants(Filter.Constants):
        model = Transactions
