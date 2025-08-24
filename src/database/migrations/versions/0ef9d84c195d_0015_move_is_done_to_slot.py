"""0015_move_is_done_to_slot

Revision ID: 0ef9d84c195d
Revises: f98baba23ac9
Create Date: 2025-08-18 17:31:16.607003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ef9d84c195d'
down_revision: Union[str, None] = 'f98baba23ac9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('bookings', 'is_done')
    op.add_column('slots', sa.Column('is_done', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('slots', 'is_done')
    op.add_column('bookings', sa.Column('is_done', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
