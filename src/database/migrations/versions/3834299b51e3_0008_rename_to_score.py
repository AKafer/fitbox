"""0008_rename_to_score

Revision ID: 3834299b51e3
Revises: 632500fbb155
Create Date: 2025-06-24 09:38:11.353422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3834299b51e3'
down_revision: Union[str, None] = '632500fbb155'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE "user" RENAME COLUMN count_trainings TO score')


def downgrade() -> None:
    op.execute('ALTER TABLE "user" RENAME COLUMN score TO count_trainings')
