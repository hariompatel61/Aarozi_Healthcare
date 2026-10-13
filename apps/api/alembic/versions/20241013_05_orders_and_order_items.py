"""Add orders and order_items tables

Revision ID: 20241013_05
Revises: 20241013_04
Create Date: 2024-10-13 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20241013_05'
down_revision: Union[str, None] = '20241013_04_profiles_and_packages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=36), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('patient_id', sa.String(length=36), sa.ForeignKey('patients.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('order_no', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('referral_partner_id', sa.String(length=36), nullable=True),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'order_no', name='uq_orders_tenant_order_no'),
    )
    op.create_index('ix_orders_tenant_id', 'orders', ['tenant_id'])
    op.create_index('ix_orders_branch_id', 'orders', ['branch_id'])
    op.create_index('ix_orders_patient_id', 'orders', ['patient_id'])
    op.create_index('ix_orders_tenant_order_no', 'orders', ['tenant_id', 'order_no'])
    op.create_index('ix_orders_tenant_status', 'orders', ['tenant_id', 'status'])
    op.create_index('ix_orders_tenant_patient', 'orders', ['tenant_id', 'patient_id'])
    op.create_index('ix_orders_tenant_branch_status', 'orders', ['tenant_id', 'branch_id', 'status'])

    op.create_table(
        'order_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_id', sa.String(length=36), sa.ForeignKey('tests.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('profile_name', sa.String(length=255), nullable=True),
        sa.Column('package_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='draft'),
        sa.Column('price', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('discount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('tax', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('final_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.0'),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_test_id', 'order_items', ['test_id'])
    op.create_index('ix_order_items_status', 'order_items', ['status'])


def downgrade() -> None:
    op.drop_table('order_items')
    op.drop_table('orders')
