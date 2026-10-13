"""Add blood_unit_tests table for TTI/Testing (P07-05)

Revision ID: 20241013_26
Revises: 20241013_25
Create Date: 2024-10-13 23:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_26'
down_revision: Union[str, None] = '20241013_25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'blood_unit_tests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('blood_unit_id', sa.String(length=36), sa.ForeignKey('blood_units.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_code', sa.String(length=50), nullable=False),
        sa.Column('result', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, default='pending'),
        sa.Column('verified_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_blood_unit_tests_tenant_id', 'blood_unit_tests', ['tenant_id'])
    op.create_index('ix_blood_unit_tests_blood_unit_id', 'blood_unit_tests', ['blood_unit_id'])


def downgrade() -> None:
    op.drop_table('blood_unit_tests')
