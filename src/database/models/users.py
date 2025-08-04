from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime

from database.orm import BaseModel
from dependencies import get_db_session


class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class User(SQLAlchemyBaseUserTableUUID, BaseModel):
    email: Mapped[str] = mapped_column(
        String(length=320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=320), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=320), nullable=False)
    father_name: Mapped[str] = mapped_column(String(length=320), nullable=True)
    phone: Mapped[str] = mapped_column(String(length=320), nullable=True)
    telegram_id: Mapped[str] = mapped_column(String(length=320), nullable=True)
    photo_url: Mapped[str] = mapped_column(String(length=1024), nullable=True, default=None)
    gender: Mapped[str] = mapped_column(
        String(length=10), nullable=True, default=None
    )
    date_of_birth: Mapped[str] = mapped_column(
        Date, nullable=True, default=None
    )
    score: Mapped[int] = mapped_column(
        Integer, nullable=True, default=0
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), onupdate=utcnow(), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    bookings = relationship(
        'Bookings',
        back_populates='user',
        lazy='selectin',
        cascade='all, delete, delete-orphan',
        single_parent=True,
    )

    records = relationship(
        'Records',
        back_populates='user',
        lazy='selectin',
        cascade='all, delete, delete-orphan',
        single_parent=True,
    )

    transactions = relationship(
        'Transactions',
        back_populates='user',
        lazy='selectin',
        cascade='all, delete, delete-orphan',
        single_parent=True,
    )


async def get_user_db(session: AsyncSession = Depends(get_db_session)):
    yield SQLAlchemyUserDatabase(session, User)
