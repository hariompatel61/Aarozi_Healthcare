"""Add results and result_values tables

Revision ID: 20241013_14
Revises: 20241013_13
Create Date: 2024-10-14 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_14'
down_revision: Union[str, None] = '20241013_13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'results',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_item_id', sa.String(length=36), sa.ForeignKey('order_items.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sample_id', sa.String(length=36), sa.ForeignKey('samples.id', ondelete='SET NULL'), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('entered_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('entered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('amendment_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('order_item_id', 'version', name='uq_results_order_item_version'),
    )
    op.create_index('ix_results_tenant_id', 'results', ['tenant_id'])
    op.create_index('ix_results_order_item_id', 'results', ['order_item_id'])
    op.create_index('ix_results_tenant_status', 'results', ['tenant_id', 'status'])

    op.create_table(
        'result_values',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('result_id', sa.String(length=36), sa.ForeignKey('results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analyte_code', sa.String(length=64), nullable=False),
        sa.Column('analyte_name', sa.String(length=255), nullable=True),
        sa.Column('raw_value', sa.String(length=255), nullable=True),
        sa.Column('numeric_value', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('reference_text', sa.Text(), nullable=True),
        sa.Column('reference_range_id', sa.String(length=36), sa.ForeignKey('test_reference_ranges.id', ondelete='SET NULL'), nullable=True),
        sa.Column('abnormal_flag', sa.String(length=30), nullable=True),
        sa.Column('critical_flag', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_result_values_result_id', 'result_values', ['result_id'])
    op.create_index('ix_result_values_analyte_code', 'result_values', ['analyte_code'])


def downgrade() -> None:
    op.drop_table('result_values')
    op.drop_table('results')
