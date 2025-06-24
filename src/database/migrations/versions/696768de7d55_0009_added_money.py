"""0009_added_money

Revision ID: 696768de7d55
Revises: 3834299b51e3
Create Date: 2025-06-24 10:32:53.983864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '696768de7d55'
down_revision: Union[str, None] = '3834299b51e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transactions', sa.Column('money_amount', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transactions', 'money_amount')
