import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.orm import BaseModel


class Slots(BaseModel):
    __tablename__ = 'slots'

    id = sa.Column(sa.BigInteger, primary_key=True)
    type = sa.Column(sa.String(64), nullable=True)
    time = sa.Column(sa.DateTime(timezone=True), nullable=False)
    number_of_places = sa.Column(sa.Integer, nullable=False, default=0)
    free_places = sa.Column(sa.Integer, nullable=False, default=0)

    bookings = relationship(
        "Bookings",
        back_populates="slot",
        lazy='selectin',
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )
