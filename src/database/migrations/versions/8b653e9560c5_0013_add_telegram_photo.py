"""0013_add_telegram_photo

Revision ID: 8b653e9560c5
Revises: 2acf1054c474
Create Date: 2025-08-03 12:46:27.487665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b653e9560c5'
down_revision: Union[str, None] = '2acf1054c474'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('telegram_id', sa.String(length=320), nullable=True))
    op.add_column('user', sa.Column('photo_url', sa.String(length=1024), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'photo_url')
    op.drop_column('user', 'telegram_id')
