"""0011_added_sprints

Revision ID: 33fed4fde1cd
Revises: 6e309011d674
Create Date: 2025-07-20 13:17:05.514659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '33fed4fde1cd'
down_revision: Union[str, None] = '6e309011d674'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sprints',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('slot_id', sa.BigInteger(), nullable=False),
    sa.Column('sensor_id', sa.String(length=128), nullable=True),
    sa.Column('sprint_id', sa.Integer(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['slot_id'], ['slots.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slot_id', 'sensor_id', 'sprint_id', name='uix_sprint_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sprints')
