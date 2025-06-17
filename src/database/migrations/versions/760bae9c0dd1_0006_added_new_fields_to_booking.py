"""0006_added new fields to booking

Revision ID: 760bae9c0dd1
Revises: 1fc703a9c018
Create Date: 2025-06-17 19:36:27.555645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '760bae9c0dd1'
down_revision: Union[str, None] = '1fc703a9c018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('is_done', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('bookings', sa.Column('power', sa.Float(), nullable=True))
    op.add_column('bookings', sa.Column('energy', sa.Float(), nullable=True))
    op.add_column('bookings', sa.Column('tempo', sa.Float(), nullable=True))
    op.create_unique_constraint('uix_user_slot', 'bookings', ['user_id', 'slot_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uix_user_slot', 'bookings', type_='unique')
    op.drop_column('bookings', 'tempo')
    op.drop_column('bookings', 'energy')
    op.drop_column('bookings', 'power')
    op.drop_column('bookings', 'is_done')
