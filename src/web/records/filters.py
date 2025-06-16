from datetime import datetime

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from database.models import Records


class RecordsFilter(Filter):
    user_id__in: list[str] | None = Field(default=None)
    time__gt: datetime | None = Field(default=None)
    time__lt: datetime | None = Field(default=None)

    class Constants(Filter.Constants):
        model = Records
