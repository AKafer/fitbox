import sqlalchemy as sa
from sqlalchemy.orm import relationship

from database.orm import BaseModel


class Transactions(BaseModel):
    __tablename__ = 'transactions'

    id = sa.Column(sa.BigInteger, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    user_id = sa.Column(
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    count = sa.Column(sa.Integer, nullable=False)
    payment_method = sa.Column(sa.String(128), nullable=True)


    user = relationship(
        "User",
        back_populates="transactions",
        lazy='selectin',
        passive_deletes=True
    )
