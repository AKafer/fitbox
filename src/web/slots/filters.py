from datetime import datetime

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from database.models import Slots


class SlotsFilter(Filter):
    time__gt: datetime | None = Field(default=None)
    time__lt: datetime | None = Field(default=None)

    class Constants(Filter.Constants):
        model = Slots