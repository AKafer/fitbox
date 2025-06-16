import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.orm import BaseModel


class Records(BaseModel):
    __tablename__ = 'records'

    id = sa.Column(sa.BigInteger, primary_key=True)
    date = sa.Column(sa.Date, nullable=False)
    weight = sa.Column(sa.Float, nullable=False)
    user_id = sa.Column(
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="records",
        lazy='selectin',
        passive_deletes=True
    )
