"""Manually add duration_seconds to record

Revision ID: 2816e262078f
Revises: aafaf157ff08
Create Date: 2025-07-15 00:58:28.496582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2816e262078f'
down_revision: Union[str, None] = 'aafaf157ff08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('record', sa.Column('duration_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('record', 'duration_seconds')