"""Add context, age_unit, priority, effective dates to test_reference_ranges

Revision ID: 20241013_13
Revises: 20241013_12
Create Date: 2024-10-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_13'
down_revision: Union[str, None] = '20241013_12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('test_reference_ranges') as batch_op:
        batch_op.add_column(sa.Column('age_unit', sa.String(length=20), nullable=False, server_default='years'))
        batch_op.add_column(sa.Column('context', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=False, server_default='100'))
        batch_op.create_index('ix_test_ref_ranges_lookup', ['test_id', 'sex', 'context'])


def downgrade() -> None:
    with op.batch_alter_table('test_reference_ranges') as batch_op:
        batch_op.drop_index('ix_test_ref_ranges_lookup')
        batch_op.drop_column('priority')
        batch_op.drop_column('context')
        batch_op.drop_column('age_unit')
