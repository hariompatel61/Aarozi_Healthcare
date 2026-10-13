"""Add amended_from_id column to results

Revision ID: 20241013_17
Revises: 20241013_16
Create Date: 2024-10-14 04:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_17'
down_revision: Union[str, None] = '20241013_16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('results') as batch_op:
        batch_op.add_column(sa.Column('amended_from_id', sa.String(length=36), sa.ForeignKey('results.id', ondelete='SET NULL'), nullable=True))
        batch_op.create_index('ix_results_amended_from', ['amended_from_id'])


def downgrade() -> None:
    with op.batch_alter_table('results') as batch_op:
        batch_op.drop_index('ix_results_amended_from')
        batch_op.drop_column('amended_from_id')
