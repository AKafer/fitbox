import sqlalchemy as sa
from database.orm import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship


class Sprints(BaseModel):
    __tablename__ = 'sprints'

    id = sa.Column(sa.BigInteger, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    slot_id = sa.Column(
        sa.ForeignKey('slots.id', ondelete='CASCADE'), nullable=False
    )
    sensor_id = sa.Column(sa.String(128), nullable=True)
    sprint_id = sa.Column(sa.Integer, nullable=False)
    data = sa.Column(
        MutableDict.as_mutable(JSONB),
        nullable=True,
        default=dict,
    )
    result = sa.Column(
        MutableDict.as_mutable(JSONB),
        nullable=True,
        default=dict,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            'slot_id', 'sensor_id', 'sprint_id', name='uix_sprint_id'
        ),
    )

    slot = relationship(
        'Slots',
        back_populates='sprints',
        lazy='selectin',
        passive_deletes=True,
    )
