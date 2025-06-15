import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.orm import BaseModel


class Bookings(BaseModel):
    __tablename__ = 'bookings'

    id = sa.Column(sa.BigInteger, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    source_record = sa.Column(sa.String(64), nullable=True)
    user_id = sa.Column(
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    slot_id = sa.Column(
        sa.ForeignKey("slots.id", ondelete="CASCADE"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="bookings",
        lazy='selectin',
        passive_deletes=True
    )

    slot = relationship(
        "Slots",
        back_populates="bookings",
        lazy='selectin',
        passive_deletes=True
    )


