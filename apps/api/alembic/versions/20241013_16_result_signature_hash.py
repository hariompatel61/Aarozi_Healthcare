"""Add signature_hash column to results

Revision ID: 20241013_16
Revises: 20241013_15
Create Date: 2024-10-14 03:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_16'
down_revision: Union[str, None] = '20241013_15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('results') as batch_op:
        batch_op.add_column(sa.Column('signature_hash', sa.String(length=128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('results') as batch_op:
        batch_op.drop_column('signature_hash')
