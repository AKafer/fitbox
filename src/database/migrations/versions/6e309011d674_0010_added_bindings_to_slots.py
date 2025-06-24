"""0010_added_bindings_to_slots

Revision ID: 6e309011d674
Revises: 696768de7d55
Create Date: 2025-06-24 11:20:43.804990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6e309011d674'
down_revision: Union[str, None] = '696768de7d55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('sensor_id', sa.String(length=128), nullable=True))
    op.add_column('slots', sa.Column('bindings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('slots', 'bindings')
    op.drop_column('bookings', 'sensor_id')
