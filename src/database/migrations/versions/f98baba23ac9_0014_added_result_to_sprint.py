"""0014_added_result_to_sprint

Revision ID: f98baba23ac9
Revises: 8b653e9560c5
Create Date: 2025-08-14 11:10:37.262573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f98baba23ac9'
down_revision: Union[str, None] = '8b653e9560c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sprints', sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sprints', 'result')
