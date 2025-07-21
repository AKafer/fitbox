"""0012 added sprints_data to booking

Revision ID: 2acf1054c474
Revises: 33fed4fde1cd
Create Date: 2025-07-21 19:18:56.473939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2acf1054c474'
down_revision: Union[str, None] = '33fed4fde1cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('sprints_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'sprints_data')
