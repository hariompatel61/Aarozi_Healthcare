"""Add blood_movements table for traceability

Revision ID: 20241013_25
Revises: 20241013_24
Create Date: 2024-10-13 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_25'
down_revision: Union[str, None] = '20241013_24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'blood_movements',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('blood_unit_id', sa.String(length=36), sa.ForeignKey('blood_units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('movement_type', sa.String(length=50), nullable=False),
        sa.Column('from_status', sa.String(length=30), nullable=True),
        sa.Column('to_status', sa.String(length=30), nullable=False),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('actor_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_blood_movements_tenant_id', 'blood_movements', ['tenant_id'])
    op.create_index('ix_blood_movements_blood_unit_id', 'blood_movements', ['blood_unit_id'])


def downgrade() -> None:
    op.drop_table('blood_movements')
