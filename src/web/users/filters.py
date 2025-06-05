from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from database.models import User


class UsersFilter(Filter):
    id__in: list[str] | None = Field(default=None)
    email__ilike: str | None = Field(default=None)
    name__ilike: str | None = Field(default=None)
    last_name__ilike: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    gender: str | None = Field(default=None)

    class Constants(Filter.Constants):
        model = User
