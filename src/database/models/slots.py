import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from database.orm import BaseModel


class Slots(BaseModel):
    __tablename__ = 'slots'

    id = sa.Column(sa.BigInteger, primary_key=True)
    type = sa.Column(sa.String(64), nullable=True)
    time = sa.Column(sa.DateTime(timezone=True), nullable=False)
    number_of_places = sa.Column(sa.Integer, nullable=False, default=0)
    free_places = sa.Column(sa.Integer, nullable=False, default=0)
    bindings = sa.Column(
        MutableDict.as_mutable(JSONB),
        nullable=True,
        default=dict,
    )

    bookings = relationship(
        "Bookings",
        back_populates="slot",
        lazy='selectin',
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )

    sprints = relationship(
        "Sprints",
        back_populates="slot",
        lazy='selectin',
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )
