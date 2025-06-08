"""0003_added_slots

Revision ID: 7e34a5644747
Revises: 56e7eb15bb0a
Create Date: 2025-06-08 13:35:25.405099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e34a5644747'
down_revision: Union[str, None] = '56e7eb15bb0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('slots',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('type', sa.String(length=64), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.Column('number_of_places', sa.Integer(), nullable=False),
    sa.Column('free_places', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('slots')
